from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from contas.services import EnviadorEmMemoria

Usuario = get_user_model()

DADOS_FORM = {
    "nome_completo": "Maria da Silva",
    "email": "maria@exemplo.com",
    "celular": "(82) 98765-4321",
    "senha": "senhaforte1",
    "confirmacao_senha": "senhaforte1",
    "locomocao": "",
    "aceite_termos": "on",
}


@override_settings(ENVIADOR_DE_CODIGO="contas.services.enviadores.EnviadorEmMemoria")
class CadastroEVerificacaoViewTests(TestCase):
    def setUp(self):
        EnviadorEmMemoria.limpar()

    def test_cadastro_valido_redireciona_e_verificacao_correta_autentica(self):
        resposta = self.client.post(reverse("contas:cadastro"), DADOS_FORM)

        self.assertRedirects(resposta, reverse("contas:verificar"))
        _, codigo = EnviadorEmMemoria.enviados[-1]

        resposta = self.client.post(reverse("contas:verificar"), {"codigo": codigo})

        self.assertRedirects(resposta, reverse("trechos:mapa"))
        usuario = Usuario.objects.get(email="maria@exemplo.com")
        self.assertEqual(int(self.client.session["_auth_user_id"]), usuario.pk)
        self.assertNotIn("cadastro_pendente_id", self.client.session)

    def test_cadastro_com_email_repetido_mostra_erro_no_campo(self):
        self.client.post(reverse("contas:cadastro"), DADOS_FORM)

        resposta = self.client.post(
            reverse("contas:cadastro"), {**DADOS_FORM, "celular": "82911112222"}
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Já existe uma conta com este e-mail.", resposta.context["form"].errors["email"])

    def test_verificar_sem_cadastro_pendente_redireciona_para_o_cadastro(self):
        resposta = self.client.get(reverse("contas:verificar"))

        self.assertRedirects(resposta, reverse("contas:cadastro"))


class EntrarESairViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.verificado = Usuario.objects.create_user(
            "ana@exemplo.com",
            "senhaforte1",
            nome_completo="Ana Souza",
            celular="82911111111",
            celular_verificado=True,
            is_active=True,
        )
        Usuario.objects.create_user(
            "pendente@exemplo.com", "senhaforte1", nome_completo="Pedro Lima", celular="82922222222"
        )

    def test_conta_nao_verificada_nao_consegue_entrar(self):
        resposta = self.client.post(
            reverse("contas:entrar"), {"username": "pendente@exemplo.com", "password": "senhaforte1"}
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_next_externo_e_ignorado_no_login(self):
        resposta = self.client.post(
            reverse("contas:entrar"),
            {"username": "ana@exemplo.com", "password": "senhaforte1", "next": "https://malicioso.com/"},
        )

        self.assertRedirects(resposta, reverse("trechos:mapa"))

    def test_next_interno_e_respeitado_no_login(self):
        resposta = self.client.post(
            reverse("contas:entrar"),
            {"username": "ANA@exemplo.com", "password": "senhaforte1", "next": "/cadastro/"},
        )

        self.assertRedirects(resposta, "/cadastro/", fetch_redirect_response=False)

    def test_post_em_sair_encerra_a_sessao_e_get_retorna_405(self):
        self.client.force_login(self.verificado)

        self.assertEqual(self.client.get(reverse("contas:sair")).status_code, 405)

        resposta = self.client.post(reverse("contas:sair"))

        self.assertRedirects(resposta, reverse("trechos:mapa"))
        self.assertNotIn("_auth_user_id", self.client.session)
