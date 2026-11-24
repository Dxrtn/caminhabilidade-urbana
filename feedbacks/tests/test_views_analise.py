from django.test import Client
from django.urls import reverse

from feedbacks.models import Feedback, StatusFeedback
from feedbacks.tests.base import TesteComMidia, imagem_de_teste
from feedbacks.tests.fabrica import criar_feedback, criar_foto
from trechos.models import Classificacao, Obstaculo
from trechos.tests.fabrica import criar_trecho, criar_usuario


class AcessoAAnaliseTests(TesteComMidia):
    @classmethod
    def setUpTestData(cls):
        feedback = criar_feedback(criar_usuario(), criar_trecho())
        cls.rotas = [
            reverse("feedbacks:fila"),
            reverse("feedbacks:analisar", args=[feedback.pk]),
            reverse("feedbacks:aceitar", args=[feedback.pk]),
            reverse("feedbacks:rejeitar", args=[feedback.pk]),
        ]

    def test_visitante_e_redirecionado_e_usuario_comum_recebe_403(self):
        for rota in self.rotas:
            with self.subTest(rota=rota, quem="visitante"):
                self.assertRedirects(self.client.get(rota), f"{reverse('contas:entrar')}?next={rota}")

        self.client.force_login(criar_usuario())
        for rota in self.rotas:
            with self.subTest(rota=rota, quem="comum"):
                self.assertEqual(self.client.get(rota).status_code, 403)
                self.assertEqual(self.client.post(rota).status_code, 403)


class AnalisePeloAdministradorTests(TesteComMidia):
    @classmethod
    def setUpTestData(cls):
        cls.administrador = criar_usuario(is_staff=True)

    def setUp(self):
        self.client.force_login(self.administrador)

    def test_painel_mostra_o_link_da_fila_com_a_contagem(self):
        criar_feedback(criar_usuario(), criar_trecho())
        criar_feedback(criar_usuario(), criar_trecho())

        resposta = self.client.get(reverse("trechos:painel"))

        self.assertContains(resposta, reverse("feedbacks:fila"))
        self.assertContains(resposta, '<span class="contador">2</span>', html=True)

    def test_fila_e_tela_de_analise_abrem_com_o_aviso_sobre_fotos(self):
        feedback = criar_feedback(criar_usuario(), criar_trecho())
        criar_foto(feedback, aprovada=False)

        self.assertContains(self.client.get(reverse("feedbacks:fila")), feedback.trecho.logradouro)
        analise = self.client.get(reverse("feedbacks:analisar", args=[feedback.pk]))
        self.assertContains(analise, "Não aprove fotos em que apareçam rostos ou placas de veículos.")

    def test_get_em_aceitar_e_rejeitar_retorna_405(self):
        feedback = criar_feedback(criar_usuario(), criar_trecho())

        self.assertEqual(self.client.get(reverse("feedbacks:aceitar", args=[feedback.pk])).status_code, 405)
        self.assertEqual(self.client.get(reverse("feedbacks:rejeitar", args=[feedback.pk])).status_code, 405)

    def test_rejeitar_pela_tela_volta_para_a_fila(self):
        feedback = criar_feedback(criar_usuario(), criar_trecho())

        resposta = self.client.post(reverse("feedbacks:rejeitar", args=[feedback.pk]), {"motivo": "DUPLICADO", "texto": ""})

        self.assertRedirects(resposta, reverse("feedbacks:fila"))
        feedback.refresh_from_db()
        self.assertEqual(feedback.status, StatusFeedback.REJEITADO)

    def test_rejeitar_outro_sem_texto_mostra_o_erro(self):
        feedback = criar_feedback(criar_usuario(), criar_trecho())

        resposta = self.client.post(reverse("feedbacks:rejeitar", args=[feedback.pk]), {"motivo": "OUTRO", "texto": ""})

        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context["form_rejeitar"].errors)

    def test_aceitar_ja_analisado_mostra_erro_e_volta_para_a_fila(self):
        feedback = criar_feedback(criar_usuario(), criar_trecho(), status=StatusFeedback.ACEITO)

        resposta = self.client.post(reverse("feedbacks:aceitar", args=[feedback.pk]), {"nova_classificacao": ""}, follow=True)

        self.assertRedirects(resposta, reverse("feedbacks:fila"))
        self.assertContains(resposta, "já foi analisado")


class FluxoCompletoTests(TesteComMidia):
    def test_usuario_envia_administrador_aceita_e_a_api_mostra_a_nova_classificacao(self):
        trecho = criar_trecho(classificacao=Classificacao.ACESSIVEL)
        usuario = Client()
        usuario.force_login(criar_usuario())
        administrador = Client()
        administrador.force_login(criar_usuario(is_staff=True))

        envio = usuario.post(
            reverse("feedbacks:enviar", args=[trecho.pk]),
            {
                "tipo": "NOVO_PROBLEMA",
                "obstaculos": [Obstaculo.objects.get(codigo="obra").pk],
                "classificacao_sugerida": "INACESSIVEL",
                "descricao": "Obra ocupando toda a calçada.",
                "fotos": [imagem_de_teste()],
            },
        )
        self.assertRedirects(envio, reverse("trechos:detalhe", args=[trecho.pk]))
        feedback = Feedback.objects.get(trecho=trecho)
        foto = feedback.fotos.get()

        aceite = administrador.post(
            reverse("feedbacks:aceitar", args=[feedback.pk]),
            {"nova_classificacao": "INACESSIVEL", "obstaculos": ["obra"], "fotos_aprovadas": [foto.pk]},
        )
        self.assertRedirects(aceite, reverse("feedbacks:fila"))

        api = usuario.get(reverse("trechos:api_trechos")).json()["trechos"]
        self.assertEqual([t["classificacao"] for t in api if t["id"] == trecho.pk], ["INACESSIVEL"])
        detalhe = usuario.get(reverse("trechos:detalhe", args=[trecho.pk]))
        self.assertContains(detalhe, foto.imagem.url)  # a foto aprovada ficou pública
        meus = usuario.get(reverse("feedbacks:meus"))
        self.assertContains(meus, "foi aceito. Obrigado!")
