from django.test import TestCase
from django.urls import reverse

from feedbacks.tests.fabrica import criar_feedback
from trechos.models import Classificacao, Obstaculo, TrechoObstaculo
from trechos.tests.fabrica import criar_trecho, criar_usuario


class MapaViewTests(TestCase):
    def test_pagina_inicial_abre_para_visitante_e_inclui_o_leaflet(self):
        resposta = self.client.get(reverse("trechos:mapa"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "unpkg.com/leaflet@1.9.4/dist/leaflet.js")
        self.assertContains(resposta, 'integrity="sha256-')
        self.assertContains(resposta, 'id="mapa"')
        self.assertContains(resposta, 'value="degrau"')  # obstáculos do filtro, vindos do service
        self.assertNotContains(resposta, "Mapa em construção")


class TrechosApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.acessivel = criar_trecho(classificacao=Classificacao.ACESSIVEL)
        cls.inacessivel = criar_trecho(classificacao=Classificacao.INACESSIVEL)
        TrechoObstaculo.objects.create(trecho=cls.inacessivel, obstaculo=Obstaculo.objects.get(codigo="obra"))

    def test_retorna_json_com_os_trechos_e_aplica_os_filtros(self):
        todos = self.client.get(reverse("trechos:api_trechos")).json()["trechos"]
        por_classificacao = self.client.get(reverse("trechos:api_trechos"), {"classificacao": "ACESSIVEL"}).json()
        por_obstaculo = self.client.get(reverse("trechos:api_trechos"), {"obstaculo": "obra"}).json()

        self.assertEqual(len(todos), 2)
        self.assertEqual([t["id"] for t in por_classificacao["trechos"]], [self.acessivel.pk])
        self.assertEqual([t["id"] for t in por_obstaculo["trechos"]], [self.inacessivel.pk])


class BuscaApiTests(TestCase):
    def test_texto_curto_retorna_lista_vazia_com_aviso(self):
        resposta = self.client.get(reverse("trechos:api_busca"), {"q": "ab"})

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), {"resultados": [], "aviso": "Digite ao menos 3 letras."})

    def test_busca_valida_retorna_resultados(self):
        criar_trecho(logradouro="Avenida Álvaro Otacílio")

        resultados = self.client.get(reverse("trechos:api_busca"), {"q": "álvaro"}).json()["resultados"]

        self.assertEqual([r["logradouro"] for r in resultados], ["Avenida Álvaro Otacílio"])


class TrechoDetalheViewTests(TestCase):
    def test_trecho_ativo_retorna_200_com_texto_para_voz(self):
        trecho = criar_trecho(logradouro="Rua X", referencia_inicio="Rua A", referencia_fim="Rua B", classificacao=Classificacao.PARCIAL)
        for codigo in ("degrau", "poste-placa"):
            TrechoObstaculo.objects.create(trecho=trecho, obstaculo=Obstaculo.objects.get(codigo=codigo))

        resposta = self.client.get(reverse("trechos:detalhe", args=[trecho.pk]))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(
            resposta,
            "Rua X, entre Rua A e Rua B, lado par. Classificação: parcialmente acessível. "
            "Obstáculos: degrau ou desnível e poste ou placa. Atualizado em ",
        )
        self.assertContains(resposta, f"?trecho={trecho.pk}")  # Voltar ao mapa

    def test_trecho_inativo_retorna_404(self):
        trecho = criar_trecho(ativo=False)

        self.assertEqual(self.client.get(reverse("trechos:detalhe", args=[trecho.pk])).status_code, 404)

    def test_texto_de_relato_com_script_aparece_escapado(self):
        trecho = criar_trecho()
        criar_feedback(criar_usuario(), trecho, descricao="<script>alert('x')</script> calçada quebrada")

        resposta = self.client.get(reverse("trechos:detalhe", args=[trecho.pk]))

        self.assertNotContains(resposta, "<script>alert('x')</script>")
        self.assertContains(resposta, "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt; calçada quebrada")
