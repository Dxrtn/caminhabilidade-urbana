from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import path
from django.views import View

from comum.mixins import AdministradorRequeridoMixin


class AreaRestritaView(AdministradorRequeridoMixin, View):
    def get(self, request):
        return HttpResponse("ok")


urlpatterns = [path("restrita/", AreaRestritaView.as_view(), name="restrita")]

# A rota contas:entrar só existe a partir da spec 0002; aqui basta um caminho fixo.
LOGIN_DE_TESTE = "/entrar-teste/"


@override_settings(ROOT_URLCONF=__name__, LOGIN_URL=LOGIN_DE_TESTE)
class AdministradorRequeridoMixinTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Usuario = get_user_model()
        cls.comum = Usuario.objects.create_user(
            "comum@exemplo.com",
            "senha-forte-123",
            nome_completo="Usuário Comum",
            celular="82911111111",
            celular_verificado=True,
            is_active=True,
        )
        cls.administrador = Usuario.objects.create_superuser(
            "admin@exemplo.com",
            "senha-forte-123",
            nome_completo="Administrador",
            celular="82922222222",
        )

    def test_visitante_e_redirecionado_ao_login(self):
        resposta = self.client.get("/restrita/")

        self.assertRedirects(
            resposta, f"{LOGIN_DE_TESTE}?next=/restrita/", fetch_redirect_response=False
        )

    def test_usuario_comum_recebe_403(self):
        self.client.force_login(self.comum)

        resposta = self.client.get("/restrita/")

        self.assertEqual(resposta.status_code, 403)

    def test_administrador_acessa(self):
        self.client.force_login(self.administrador)

        resposta = self.client.get("/restrita/")

        self.assertEqual(resposta.status_code, 200)
