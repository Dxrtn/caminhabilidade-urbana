from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from feedbacks.models import Feedback
from feedbacks.services import NotificacaoService
from feedbacks.tests.base import TesteComMidia, imagem_de_teste
from feedbacks.tests.fabrica import criar_feedback
from trechos.models import Obstaculo
from trechos.tests.fabrica import criar_trecho, criar_usuario


class AcessoTests(TesteComMidia):
    def test_visitante_vai_ao_login_no_formulario_e_em_meus_feedbacks(self):
        trecho = criar_trecho()
        for rota in [reverse("feedbacks:enviar", args=[trecho.pk]), reverse("feedbacks:meus")]:
            with self.subTest(rota=rota):
                resposta = self.client.get(rota)

                self.assertRedirects(resposta, f"{reverse('contas:entrar')}?next={rota}")

    def test_detalhe_do_trecho_mostra_enviar_feedback_com_login_e_next_para_visitante(self):
        trecho = criar_trecho()
        url_enviar = reverse("feedbacks:enviar", args=[trecho.pk])

        visitante = self.client.get(reverse("trechos:detalhe", args=[trecho.pk]))
        self.client.force_login(criar_usuario())
        usuario = self.client.get(reverse("trechos:detalhe", args=[trecho.pk]))

        self.assertContains(visitante, f"{reverse('contas:entrar')}?next={url_enviar}")
        self.assertContains(usuario, f'href="{url_enviar}"')


class EnviarFeedbackViewTests(TesteComMidia):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = criar_usuario()
        cls.trecho = criar_trecho()

    def setUp(self):
        self.client.force_login(self.usuario)

    def _dados(self, **alteracoes):
        dados = {
            "tipo": "NOVO_PROBLEMA",
            "obstaculos": [Obstaculo.objects.get(codigo="buraco").pk],
            "classificacao_sugerida": "",
            "descricao": "Buraco grande no meio da calçada.",
            "latitude": "",
            "longitude": "",
        }
        dados.update(alteracoes)
        return dados

    def test_formulario_abre_com_o_trecho_e_o_aviso_de_localizacao(self):
        resposta = self.client.get(reverse("feedbacks:enviar", args=[self.trecho.pk]))

        self.assertContains(resposta, self.trecho.logradouro)
        self.assertContains(resposta, "não é guardada")
        self.assertContains(resposta, 'capture="environment"')

    def test_envio_valido_com_imagem_redireciona_ao_detalhe_com_mensagem(self):
        resposta = self.client.post(
            reverse("feedbacks:enviar", args=[self.trecho.pk]), {**self._dados(), "fotos": [imagem_de_teste()]}, follow=True
        )

        self.assertRedirects(resposta, reverse("trechos:detalhe", args=[self.trecho.pk]))
        self.assertContains(resposta, "Feedback enviado! Ele será analisado pela nossa equipe.")
        self.assertEqual(Feedback.objects.get().fotos.count(), 1)

    def test_arquivo_que_nao_e_imagem_e_recusado(self):
        texto = SimpleUploadedFile("relato.png", b"isto nao e uma imagem", content_type="image/png")

        resposta = self.client.post(reverse("feedbacks:enviar", args=[self.trecho.pk]), {**self._dados(), "fotos": [texto]})

        self.assertEqual(resposta.status_code, 200)
        self.assertIn("fotos", resposta.context["form"].errors)
        self.assertFalse(Feedback.objects.exists())

    def test_erro_de_dominio_reexibe_o_formulario_com_a_mensagem_e_os_dados(self):
        resposta = self.client.post(reverse("feedbacks:enviar", args=[self.trecho.pk]), self._dados())  # sem foto

        self.assertEqual(resposta.status_code, 200)
        self.assertIn("ao menos 1 foto", str(resposta.context["form"].non_field_errors()))
        self.assertContains(resposta, "Buraco grande no meio da calçada.")

    def test_trecho_inativo_retorna_404(self):
        inativo = criar_trecho(ativo=False)

        self.assertEqual(self.client.get(reverse("feedbacks:enviar", args=[inativo.pk])).status_code, 404)


class MeusFeedbacksViewTests(TesteComMidia):
    def test_mostra_so_os_do_usuario_pagina_de_10_e_zera_notificacoes(self):
        usuario = criar_usuario()
        outro = criar_usuario()
        feedbacks = [criar_feedback(usuario, criar_trecho(logradouro=f"Rua Minha {n:02d}")) for n in range(12)]
        criar_feedback(outro, criar_trecho(logradouro="Rua de Outra Pessoa"))
        NotificacaoService.notificar(feedbacks[0], "Seu feedback foi aceito. Obrigado!")
        self.client.force_login(usuario)

        primeira = self.client.get(reverse("feedbacks:meus"))
        segunda = self.client.get(reverse("feedbacks:meus"), {"pagina": 2})

        self.assertEqual(len(primeira.context["pagina"].object_list), 10)
        self.assertEqual(len(segunda.context["pagina"].object_list), 2)
        self.assertNotContains(primeira, "Rua de Outra Pessoa")
        self.assertNotContains(segunda, "Rua de Outra Pessoa")
        self.assertContains(primeira, "Seu feedback foi aceito. Obrigado!")
        self.assertEqual(NotificacaoService.contar_nao_lidas(usuario), 0)
        self.assertNotContains(primeira, 'class="contador"')  # o menu já aparece zerado

    def test_contador_aparece_no_menu_com_notificacao_nao_lida(self):
        usuario = criar_usuario()
        NotificacaoService.notificar(criar_feedback(usuario, criar_trecho()), "Novidade.")
        self.client.force_login(usuario)

        resposta = self.client.get(reverse("trechos:mapa"))

        self.assertContains(resposta, 'class="contador">1<')

    def test_get_em_excluir_retorna_405_e_post_exclui(self):
        usuario = criar_usuario()
        feedback = criar_feedback(usuario, criar_trecho())
        self.client.force_login(usuario)

        self.assertEqual(self.client.get(reverse("feedbacks:excluir", args=[feedback.pk])).status_code, 405)

        resposta = self.client.post(reverse("feedbacks:excluir", args=[feedback.pk]))
        self.assertRedirects(resposta, reverse("feedbacks:meus"))
        self.assertFalse(Feedback.objects.filter(pk=feedback.pk).exists())

    def test_excluir_feedback_de_outro_usuario_retorna_404(self):
        feedback = criar_feedback(criar_usuario(), criar_trecho())
        self.client.force_login(criar_usuario())

        self.assertEqual(self.client.post(reverse("feedbacks:excluir", args=[feedback.pk])).status_code, 404)
