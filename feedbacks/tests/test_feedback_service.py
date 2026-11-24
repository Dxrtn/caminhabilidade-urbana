import os
from decimal import Decimal
from unittest import mock

from django.db import IntegrityError
from django.utils import timezone

from feedbacks.exceptions import (
    FeedbackEmAnaliseExistente,
    FeedbackIncompleto,
    FeedbackNaoEncontrado,
    FeedbackNaoPodeSerExcluido,
    FotosEmExcesso,
    LimiteDiarioAtingido,
)
from feedbacks.models import Feedback, FotoFeedback, Notificacao, StatusFeedback, TipoFeedback
from feedbacks.services import FeedbackService, NotificacaoService
from feedbacks.tests.base import TesteComMidia, imagem_de_teste
from feedbacks.tests.fabrica import criar_feedback
from trechos.exceptions import TrechoNaoEncontrado
from trechos.models import Classificacao, Obstaculo
from trechos.tests.fabrica import criar_trecho, criar_usuario

DESCRICAO = "Buraco grande perto da esquina."


class EnviarTests(TesteComMidia):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = criar_usuario()
        # Trecho de ~100 m na Pajuçara: início (-9.6690, -35.7160), fim (-9.6685, -35.7152).
        cls.trecho = criar_trecho(
            classificacao=Classificacao.ACESSIVEL,
            lat_inicio=Decimal("-9.669000"),
            lng_inicio=Decimal("-35.716000"),
            lat_fim=Decimal("-9.668500"),
            lng_fim=Decimal("-35.715200"),
        )
        cls.buraco = Obstaculo.objects.get(codigo="buraco")

    def _enviar(self, **campos):
        trecho_id = campos.pop("trecho_id", self.trecho.pk)
        dados = {
            "tipo": TipoFeedback.NOVO_PROBLEMA,
            "descricao": DESCRICAO,
            "obstaculo_ids": [self.buraco.pk],
            "fotos": [imagem_de_teste()],
        }
        dados.update(campos)
        return FeedbackService.enviar(self.usuario, trecho_id, **dados)

    def test_cria_em_analise_com_obstaculos_e_fotos_sem_alterar_o_trecho(self):
        feedback = self._enviar(classificacao_sugerida=Classificacao.INACESSIVEL)

        self.assertEqual(feedback.status, StatusFeedback.EM_ANALISE)
        self.assertEqual(list(feedback.obstaculos.all()), [self.buraco])
        self.assertEqual(feedback.fotos.count(), 1)
        self.trecho.refresh_from_db()
        self.assertEqual(self.trecho.classificacao, Classificacao.ACESSIVEL)

    def test_novo_problema_sem_foto_ou_sem_obstaculo_levanta_incompleto(self):
        with self.assertRaises(FeedbackIncompleto):
            self._enviar(fotos=[])
        with self.assertRaises(FeedbackIncompleto):
            self._enviar(obstaculo_ids=[])
        self.assertFalse(Feedback.objects.exists())

    def test_outros_tipos_nao_exigem_foto_nem_obstaculo(self):
        feedback = self._enviar(tipo=TipoFeedback.PROBLEMA_RESOLVIDO, obstaculo_ids=[], fotos=[])

        self.assertEqual(feedback.tipo, TipoFeedback.PROBLEMA_RESOLVIDO)

    def test_o_11o_feedback_do_dia_levanta_limite_diario(self):
        for _ in range(10):
            criar_feedback(self.usuario, criar_trecho())

        with self.assertRaises(LimiteDiarioAtingido):
            self._enviar()

    def test_segundo_em_analise_no_mesmo_trecho_levanta_em_analise_existente(self):
        self._enviar()

        with self.assertRaises(FeedbackEmAnaliseExistente):
            self._enviar()

    def test_integrity_error_da_constraint_vira_em_analise_existente(self):
        # Simula o envio simultâneo: a verificação passa, mas o banco recusa pela constraint.
        criar_feedback(self.usuario, self.trecho)
        with mock.patch.object(FeedbackService, "_tem_em_analise", return_value=False):
            with self.assertRaises(FeedbackEmAnaliseExistente) as contexto:
                self._enviar()
        self.assertIsInstance(contexto.exception.__cause__, IntegrityError)

    def test_mais_de_3_fotos_levanta_fotos_em_excesso(self):
        with self.assertRaises(FotosEmExcesso):
            self._enviar(fotos=[imagem_de_teste(f"f{n}.png") for n in range(4)])

    def test_distancia_marca_enviado_a_distancia_sem_guardar_a_posicao(self):
        longe = self._enviar(latitude=-9.6500, longitude=-35.7000)  # ~2,7 km
        Feedback.objects.filter(pk=longe.pk).update(status=StatusFeedback.ACEITO, analisado_em=timezone.now())
        perto = self._enviar(latitude=-9.66880, longitude=-35.71560)  # no meio do trecho
        Feedback.objects.filter(pk=perto.pk).update(status=StatusFeedback.ACEITO, analisado_em=timezone.now())
        sem_posicao = self._enviar()

        self.assertTrue(longe.enviado_a_distancia)
        self.assertFalse(perto.enviado_a_distancia)
        self.assertFalse(sem_posicao.enviado_a_distancia)
        nomes = {campo.name for campo in Feedback._meta.get_fields()}
        self.assertFalse(nomes & {"latitude", "longitude", "lat", "lng", "posicao", "localizacao"})

    def test_trecho_inativo_levanta_trecho_nao_encontrado(self):
        inativo = criar_trecho(ativo=False)

        with self.assertRaises(TrechoNaoEncontrado):
            self._enviar(trecho_id=inativo.pk)


class ListarEExcluirTests(TesteComMidia):
    @classmethod
    def setUpTestData(cls):
        cls.dono = criar_usuario()
        cls.outro = criar_usuario()

    def test_excluir_pelo_dono_em_analise_apaga_feedback_e_fotos_do_disco(self):
        feedback = criar_feedback(self.dono, criar_trecho())
        foto = FotoFeedback.objects.create(feedback=feedback, imagem=imagem_de_teste())
        caminho = foto.imagem.path

        with self.captureOnCommitCallbacks(execute=True):
            FeedbackService.excluir(feedback.pk, self.dono)

        self.assertFalse(Feedback.objects.filter(pk=feedback.pk).exists())
        self.assertFalse(FotoFeedback.objects.filter(pk=foto.pk).exists())
        self.assertFalse(os.path.exists(caminho))

    def test_excluir_de_outro_usuario_levanta_nao_encontrado(self):
        feedback = criar_feedback(self.dono, criar_trecho())

        with self.assertRaises(FeedbackNaoEncontrado):
            FeedbackService.excluir(feedback.pk, self.outro)

    def test_excluir_ja_analisado_levanta_nao_pode_ser_excluido(self):
        feedback = criar_feedback(self.dono, criar_trecho(), status=StatusFeedback.ACEITO)

        with self.assertRaises(FeedbackNaoPodeSerExcluido):
            FeedbackService.excluir(feedback.pk, self.dono)

    def test_listar_do_usuario_mostra_so_os_dele_do_mais_recente(self):
        primeiro = criar_feedback(self.dono, criar_trecho())
        segundo = criar_feedback(self.dono, criar_trecho())
        criar_feedback(self.outro, criar_trecho())

        pagina = FeedbackService.listar_do_usuario(self.dono)

        self.assertEqual(list(pagina.object_list), [segundo, primeiro])


class NotificacaoServiceTests(TesteComMidia):
    def test_conta_e_marca_como_lidas(self):
        usuario = criar_usuario()
        feedback = criar_feedback(usuario, criar_trecho())
        NotificacaoService.notificar(feedback, "Seu feedback foi aceito.")
        NotificacaoService.notificar(feedback, "Outra notificação.")

        self.assertEqual(NotificacaoService.contar_nao_lidas(usuario), 2)
        self.assertEqual(len(NotificacaoService.listar_recentes(usuario)), 2)

        NotificacaoService.marcar_todas_como_lidas(usuario)

        self.assertEqual(NotificacaoService.contar_nao_lidas(usuario), 0)

    def test_nao_notifica_feedback_sem_autor(self):
        feedback = criar_feedback(None, criar_trecho())

        self.assertIsNone(NotificacaoService.notificar(feedback, "Sem destinatário."))
        self.assertFalse(Notificacao.objects.exists())
