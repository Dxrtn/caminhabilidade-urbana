import shutil
import tempfile
from dataclasses import fields
from datetime import timedelta

from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone

from feedbacks.models import MotivoRejeicao, StatusFeedback
from feedbacks.tests.fabrica import criar_feedback, criar_foto
from trechos.exceptions import TextoDeBuscaCurto, TrechoNaoEncontrado
from trechos.models import Bairro, Classificacao, Obstaculo, Trecho, TrechoObstaculo
from trechos.services import Relato, TrechoConsultaService
from trechos.tests.fabrica import criar_trecho, criar_usuario


class ListarParaMapaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.acessivel = criar_trecho(logradouro="Rua Acessível", classificacao=Classificacao.ACESSIVEL)
        cls.parcial = criar_trecho(logradouro="Rua Parcial", classificacao=Classificacao.PARCIAL)
        cls.inativo = criar_trecho(logradouro="Rua Inativa", ativo=False)
        TrechoObstaculo.objects.create(trecho=cls.parcial, obstaculo=Obstaculo.objects.get(codigo="degrau"))

    def test_retorna_so_ativos_com_coordenadas_em_pares_de_float(self):
        trechos = TrechoConsultaService.listar_para_mapa()

        self.assertEqual({t["id"] for t in trechos}, {self.acessivel.pk, self.parcial.pk})
        coordenadas = trechos[0]["coordenadas"]
        self.assertEqual(len(coordenadas), 2)
        self.assertTrue(all(isinstance(valor, float) for par in coordenadas for valor in par))
        self.assertEqual(trechos[0]["classificacao_rotulo"], "Acessível")

    def test_filtra_por_classificacao_e_por_obstaculo(self):
        por_classificacao = TrechoConsultaService.listar_para_mapa(classificacao=Classificacao.PARCIAL)
        por_obstaculo = TrechoConsultaService.listar_para_mapa(obstaculo_codigo="degrau")
        invalida = TrechoConsultaService.listar_para_mapa(classificacao="OTIMA")

        self.assertEqual([t["id"] for t in por_classificacao], [self.parcial.pk])
        self.assertEqual([t["id"] for t in por_obstaculo], [self.parcial.pk])
        self.assertEqual(len(invalida), 2)  # classificação inválida é ignorada


class BuscarTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        jatiuca = Bairro.objects.get(nome="Jatiúca")
        for numero in range(7):
            criar_trecho(logradouro=f"Rua Jangadeiros {numero}")
        criar_trecho(logradouro="Avenida Qualquer", bairro=jatiuca)

    def test_com_menos_de_3_letras_levanta_texto_curto(self):
        with self.assertRaises(TextoDeBuscaCurto):
            TrechoConsultaService.buscar("ab")
        with self.assertRaises(TextoDeBuscaCurto):
            TrechoConsultaService.buscar(" a b ")

    def test_encontra_por_logradouro_e_bairro_e_limita_a_5(self):
        por_logradouro = TrechoConsultaService.buscar("jan")
        por_bairro = TrechoConsultaService.buscar("jatiú")

        self.assertEqual(len(por_logradouro), 5)
        self.assertEqual([r["logradouro"] for r in por_bairro], ["Avenida Qualquer"])
        self.assertEqual(len(por_bairro[0]["centro"]), 2)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="caminhabilidade-testes-"))
class ObterDetalheTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_trecho_inativo_levanta_nao_encontrado(self):
        trecho = criar_trecho(ativo=False)

        with self.assertRaises(TrechoNaoEncontrado):
            TrechoConsultaService.obter_detalhe(trecho.pk)

    def test_relatos_sem_autor_sem_fotos_em_analise_e_so_fotos_aprovadas(self):
        trecho = criar_trecho()
        em_analise = criar_feedback(criar_usuario(), trecho, descricao="Relato ainda em análise.")
        criar_foto(em_analise, aprovada=False)
        aceito = criar_feedback(criar_usuario(), trecho, status=StatusFeedback.ACEITO, descricao="Relato aceito pela equipe.")
        aprovada = criar_foto(aceito, aprovada=True)
        criar_foto(aceito, aprovada=False)
        criar_feedback(
            criar_usuario(),
            trecho,
            status=StatusFeedback.REJEITADO,
            motivo_rejeicao=MotivoRejeicao.CONTEUDO_IMPROPRIO,
            descricao="Relato rejeitado pela equipe.",
        )

        detalhe = TrechoConsultaService.obter_detalhe(trecho.pk)

        self.assertNotIn("usuario", {f.name for f in fields(Relato)})
        por_texto = {r.descricao: r for r in detalhe.relatos}
        self.assertEqual(set(por_texto), {"Relato ainda em análise.", "Relato aceito pela equipe."})
        self.assertTrue(por_texto["Relato ainda em análise."].em_analise)
        self.assertEqual(por_texto["Relato ainda em análise."].fotos, [])
        self.assertEqual([f.url for f in por_texto["Relato aceito pela equipe."].fotos], [aprovada.imagem.url])
        self.assertEqual([f.url for f in detalhe.fotos], [aprovada.imagem.url])

    def test_mostra_no_maximo_5_relatos_do_mais_recente(self):
        trecho = criar_trecho()
        for numero in range(7):
            criar_feedback(criar_usuario(), trecho, descricao=f"Relato número {numero} do trecho.")

        detalhe = TrechoConsultaService.obter_detalhe(trecho.pk)

        self.assertEqual(len(detalhe.relatos), 5)
        self.assertEqual(detalhe.relatos[0].descricao, "Relato número 6 do trecho.")

    def test_marca_desatualizado_com_mais_de_180_dias(self):
        recente = criar_trecho()
        antigo = criar_trecho()
        Trecho.objects.filter(pk=antigo.pk).update(atualizado_em=timezone.now() - timedelta(days=181))

        self.assertFalse(TrechoConsultaService.obter_detalhe(recente.pk).desatualizado)
        self.assertTrue(TrechoConsultaService.obter_detalhe(antigo.pk).desatualizado)
