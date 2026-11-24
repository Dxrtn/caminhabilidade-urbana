import shutil
import tempfile
from io import BytesIO

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from trechos.models import Bairro, Classificacao, FotoTrecho, HistoricoTrecho, Obstaculo, Trecho
from trechos.tests.fabrica import criar_trecho, criar_usuario


def _png() -> SimpleUploadedFile:
    conteudo = BytesIO()
    Image.new("RGB", (4, 4), "white").save(conteudo, format="PNG")
    return SimpleUploadedFile("calcada.png", conteudo.getvalue(), content_type="image/png")


def _dados_form(**alteracoes) -> dict:
    dados = {
        "logradouro": "Rua Jangadeiros Alagoanos",
        "bairro": Bairro.objects.get(nome="Pajuçara").pk,
        "referencia_inicio": "Esquina com a Rua A",
        "referencia_fim": "Esquina com a Rua B",
        "lado": "PAR",
        "lat_inicio": "-9.669000",
        "lng_inicio": "-35.716000",
        "lat_fim": "-9.668500",
        "lng_fim": "-35.715200",
        "classificacao": "PARCIAL",
        "obstaculos": ["lixeira"],
        "observacoes": "Lixeira no meio da calçada.",
    }
    dados.update(alteracoes)
    return dados


class AcessoAoPainelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.comum = criar_usuario()
        trecho = criar_trecho()
        cls.rotas = [
            reverse("trechos:painel"),
            reverse("trechos:gestao"),
            reverse("trechos:criar"),
            reverse("trechos:editar", args=[trecho.pk]),
            reverse("trechos:desativar", args=[trecho.pk]),
            reverse("trechos:reativar", args=[trecho.pk]),
        ]

    def test_visitante_e_redirecionado_ao_login(self):
        for rota in self.rotas:
            with self.subTest(rota=rota):
                resposta = self.client.get(rota)

                self.assertRedirects(resposta, f"{reverse('contas:entrar')}?next={rota}")

    def test_usuario_comum_recebe_403(self):
        self.client.force_login(self.comum)
        for rota in self.rotas:
            with self.subTest(rota=rota):
                self.assertEqual(self.client.get(rota).status_code, 403)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="caminhabilidade-testes-"))
class GestaoPeloAdministradorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.administrador = criar_usuario(is_staff=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.client.force_login(self.administrador)

    def test_painel_lista_e_formulario_abrem(self):
        criar_trecho()
        for rota in [reverse("trechos:painel"), reverse("trechos:gestao"), reverse("trechos:criar")]:
            with self.subTest(rota=rota):
                self.assertEqual(self.client.get(rota).status_code, 200)

    def test_administrador_cria_trecho_pelo_formulario(self):
        resposta = self.client.post(reverse("trechos:criar"), {**_dados_form(), "fotos": [_png()]})

        self.assertRedirects(resposta, reverse("trechos:gestao"))
        trecho = Trecho.objects.get(logradouro="Rua Jangadeiros Alagoanos")
        self.assertEqual(trecho.atualizado_por, self.administrador)
        self.assertEqual(list(trecho.obstaculos.all()), [Obstaculo.objects.get(codigo="lixeira")])
        self.assertEqual(FotoTrecho.objects.filter(trecho=trecho).count(), 1)

    def test_administrador_edita_trecho_e_ve_o_historico(self):
        trecho = criar_trecho(atualizado_por=self.administrador)

        resposta = self.client.post(
            reverse("trechos:editar", args=[trecho.pk]), _dados_form(classificacao="INACESSIVEL")
        )

        self.assertRedirects(resposta, reverse("trechos:gestao"))
        trecho.refresh_from_db()
        self.assertEqual(trecho.classificacao, Classificacao.INACESSIVEL)
        self.assertEqual(HistoricoTrecho.objects.filter(trecho=trecho).count(), 2)
        pagina = self.client.get(reverse("trechos:editar", args=[trecho.pk]))
        self.assertContains(pagina, "Histórico de classificação")
        self.assertContains(pagina, "INACESSIVEL")

    def test_trecho_duplicado_aparece_como_erro_do_formulario(self):
        self.client.post(reverse("trechos:criar"), _dados_form())

        resposta = self.client.post(reverse("trechos:criar"), _dados_form())

        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Já existe um trecho", str(resposta.context["form"].non_field_errors()))

    def test_coordenada_fora_de_maceio_e_inicio_igual_ao_fim_sao_recusados(self):
        fora = self.client.post(reverse("trechos:criar"), _dados_form(lat_inicio="-23.550000"))
        igual = self.client.post(reverse("trechos:criar"), _dados_form(lat_fim="-9.669000", lng_fim="-35.716000"))

        self.assertIn("lat_inicio", fora.context["form"].errors)
        self.assertTrue(igual.context["form"].non_field_errors())
        self.assertFalse(Trecho.objects.exists())

    def test_editar_trecho_inexistente_retorna_404(self):
        self.assertEqual(self.client.get(reverse("trechos:editar", args=[999999])).status_code, 404)

    def test_get_em_desativar_e_reativar_retorna_405(self):
        trecho = criar_trecho()

        self.assertEqual(self.client.get(reverse("trechos:desativar", args=[trecho.pk])).status_code, 405)
        self.assertEqual(self.client.get(reverse("trechos:reativar", args=[trecho.pk])).status_code, 405)

    def test_post_em_desativar_e_reativar_altera_o_trecho(self):
        trecho = criar_trecho()

        self.client.post(reverse("trechos:desativar", args=[trecho.pk]))
        trecho.refresh_from_db()
        self.assertFalse(trecho.ativo)

        self.client.post(reverse("trechos:reativar", args=[trecho.pk]))
        trecho.refresh_from_db()
        self.assertTrue(trecho.ativo)
