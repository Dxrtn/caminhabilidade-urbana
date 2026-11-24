from datetime import timedelta

from django.utils import timezone

from feedbacks.exceptions import FeedbackJaAnalisado, MotivoDeRejeicaoInvalido
from feedbacks.models import Feedback, FotoFeedback, MotivoRejeicao, Notificacao, StatusFeedback, TipoFeedback
from feedbacks.services import AnaliseService, FeedbackService
from feedbacks.tests.base import TesteComMidia, imagem_de_teste
from feedbacks.tests.fabrica import criar_feedback, criar_foto
from trechos.models import Classificacao, HistoricoTrecho, Obstaculo
from trechos.tests.fabrica import criar_trecho, criar_usuario


class FilaTests(TesteComMidia):
    def test_traz_so_em_analise_do_mais_antigo_para_o_mais_recente(self):
        usuario = criar_usuario()
        recente = criar_feedback(usuario, criar_trecho())
        antigo = criar_feedback(usuario, criar_trecho())
        Feedback.objects.filter(pk=antigo.pk).update(criado_em=timezone.now() - timedelta(days=3))
        criar_feedback(usuario, criar_trecho(), status=StatusFeedback.ACEITO)

        fila = AnaliseService.fila()

        self.assertEqual([f.pk for f in fila], [antigo.pk, recente.pk])
        self.assertEqual(AnaliseService.contar_em_analise(), 2)

    def test_filtra_por_tipo(self):
        usuario = criar_usuario()
        resolvido = criar_feedback(usuario, criar_trecho(), tipo=TipoFeedback.PROBLEMA_RESOLVIDO)
        criar_feedback(usuario, criar_trecho())

        self.assertEqual([f.pk for f in AnaliseService.fila(tipo=TipoFeedback.PROBLEMA_RESOLVIDO)], [resolvido.pk])


class AceitarERejeitarTests(TesteComMidia):
    @classmethod
    def setUpTestData(cls):
        cls.administrador = criar_usuario(is_staff=True)
        cls.autor = criar_usuario()

    def setUp(self):
        self.trecho = criar_trecho(classificacao=Classificacao.ACESSIVEL)
        self.feedback = criar_feedback(self.autor, self.trecho)

    def test_aceitar_com_nova_classificacao_muda_o_trecho_e_o_historico_registra_o_administrador(self):
        AnaliseService.aceitar(
            self.feedback.pk,
            self.administrador,
            nova_classificacao=Classificacao.INACESSIVEL,
            obstaculo_codigos=["buraco"],
        )

        self.trecho.refresh_from_db()
        self.assertEqual(self.trecho.classificacao, Classificacao.INACESSIVEL)
        self.assertEqual(list(self.trecho.obstaculos.values_list("codigo", flat=True)), ["buraco"])
        ultimo = HistoricoTrecho.objects.filter(trecho=self.trecho).latest("alterado_em", "id")
        self.assertEqual(ultimo.classificacao_nova, Classificacao.INACESSIVEL)
        self.assertEqual(ultimo.alterado_por, self.administrador)
        self.feedback.refresh_from_db()
        self.assertEqual(self.feedback.status, StatusFeedback.ACEITO)
        self.assertEqual(self.feedback.analisado_por, self.administrador)
        self.assertIsNotNone(self.feedback.analisado_em)

    def test_aceitar_sem_nova_classificacao_nao_cria_historico(self):
        antes = HistoricoTrecho.objects.filter(trecho=self.trecho).count()

        AnaliseService.aceitar(self.feedback.pk, self.administrador)

        self.assertEqual(HistoricoTrecho.objects.filter(trecho=self.trecho).count(), antes)
        self.trecho.refresh_from_db()
        self.assertEqual(self.trecho.classificacao, Classificacao.ACESSIVEL)

    def test_aceitar_aprova_so_as_fotos_indicadas_e_so_deste_feedback(self):
        aprovar = criar_foto(self.feedback, aprovada=False)
        manter = criar_foto(self.feedback, aprovada=False)
        de_outro = criar_foto(criar_feedback(criar_usuario(), criar_trecho()), aprovada=False)

        AnaliseService.aceitar(self.feedback.pk, self.administrador, fotos_aprovadas_ids=[aprovar.pk, de_outro.pk])

        self.assertEqual(
            set(FotoFeedback.objects.filter(aprovada=True).values_list("pk", flat=True)), {aprovar.pk}
        )
        self.assertFalse(FotoFeedback.objects.get(pk=manter.pk).aprovada)

    def test_aceitar_ou_rejeitar_ja_analisado_levanta_ja_analisado(self):
        AnaliseService.aceitar(self.feedback.pk, self.administrador)

        with self.assertRaises(FeedbackJaAnalisado):
            AnaliseService.aceitar(self.feedback.pk, self.administrador)
        with self.assertRaises(FeedbackJaAnalisado):
            AnaliseService.rejeitar(self.feedback.pk, self.administrador, MotivoRejeicao.DUPLICADO)

    def test_rejeitar_com_outro_sem_texto_levanta_motivo_invalido(self):
        with self.assertRaises(MotivoDeRejeicaoInvalido):
            AnaliseService.rejeitar(self.feedback.pk, self.administrador, MotivoRejeicao.OUTRO, texto="  ")
        with self.assertRaises(MotivoDeRejeicaoInvalido):
            AnaliseService.rejeitar(self.feedback.pk, self.administrador, "INVENTADO")

        self.feedback.refresh_from_db()
        self.assertEqual(self.feedback.status, StatusFeedback.EM_ANALISE)

    def test_rejeitar_com_outro_e_texto_grava_o_motivo(self):
        AnaliseService.rejeitar(self.feedback.pk, self.administrador, MotivoRejeicao.OUTRO, texto="Trecho errado.")

        self.feedback.refresh_from_db()
        self.assertEqual(self.feedback.status, StatusFeedback.REJEITADO)
        self.assertEqual(self.feedback.motivo_rejeicao_texto, "Trecho errado.")

    def test_aceitar_e_rejeitar_notificam_o_autor(self):
        outro = criar_feedback(self.autor, criar_trecho())

        AnaliseService.aceitar(self.feedback.pk, self.administrador)
        AnaliseService.rejeitar(outro.pk, self.administrador, MotivoRejeicao.INFORMACAO_INCORRETA)

        mensagens = list(Notificacao.objects.filter(usuario=self.autor).values_list("mensagem", flat=True))
        self.assertIn(f"Seu feedback sobre {self.trecho.logradouro} foi aceito. Obrigado!", mensagens)
        self.assertTrue(any("não foi aceito. Motivo: Informação incorreta." in m for m in mensagens))

    def test_depois_de_aceito_o_usuario_pode_enviar_outro_no_mesmo_trecho(self):
        AnaliseService.aceitar(self.feedback.pk, self.administrador)

        novo = FeedbackService.enviar(
            self.autor,
            self.trecho.pk,
            tipo=TipoFeedback.NOVO_PROBLEMA,
            descricao="Apareceu outro buraco.",
            obstaculo_ids=[Obstaculo.objects.get(codigo="buraco").pk],
            fotos=[imagem_de_teste()],
        )

        self.assertEqual(novo.status, StatusFeedback.EM_ANALISE)
