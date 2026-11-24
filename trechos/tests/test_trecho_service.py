from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from trechos.exceptions import DadosDeTrechoInvalidos, TrechoDuplicado
from trechos.models import Bairro, Classificacao, HistoricoTrecho, Lado, Trecho, TrechoMapa
from trechos.services import DadosTrecho, TrechoService
from trechos.tests.fabrica import criar_trecho, criar_usuario

DADOS = DadosTrecho(
    logradouro="Avenida Álvaro Otacílio",
    bairro="Ponta Verde",
    referencia_inicio="Esquina com a Rua A",
    referencia_fim="Esquina com a Rua B",
    lado=Lado.PAR,
    lat_inicio=Decimal("-9.665800"),
    lng_inicio=Decimal("-35.705300"),
    lat_fim=Decimal("-9.664900"),
    lng_fim=Decimal("-35.705600"),
    classificacao=Classificacao.PARCIAL,
    obstaculos=("buraco", "poste-placa"),
    observacoes="Buraco perto da esquina.",
)


class TrechoServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.administrador = criar_usuario(is_staff=True)

    def test_criar_grava_obstaculos_autor_e_historico_inicial(self):
        trecho = TrechoService.criar(DADOS, self.administrador)

        self.assertEqual(trecho.bairro.nome, "Ponta Verde")
        self.assertEqual(trecho.atualizado_por, self.administrador)
        self.assertEqual(set(trecho.obstaculos.values_list("codigo", flat=True)), {"buraco", "poste-placa"})
        historico = HistoricoTrecho.objects.get(trecho=trecho)
        self.assertIsNone(historico.classificacao_anterior)
        self.assertEqual(historico.classificacao_nova, Classificacao.PARCIAL)
        self.assertEqual(historico.alterado_por, self.administrador)

    def test_criar_com_bairro_inexistente_levanta_dados_invalidos(self):
        with self.assertRaises(DadosDeTrechoInvalidos):
            TrechoService.criar(replace(DADOS, bairro="Bairro Inventado"), self.administrador)

        self.assertFalse(Trecho.objects.exists())

    def test_criar_trecho_repetido_levanta_duplicado(self):
        TrechoService.criar(DADOS, self.administrador)

        with self.assertRaises(TrechoDuplicado):
            TrechoService.criar(DADOS, self.administrador)

    def test_atualizar_mudando_a_classificacao_gera_historico_com_o_administrador(self):
        trecho = TrechoService.criar(DADOS, criar_usuario(is_staff=True))

        TrechoService.atualizar(
            trecho.pk, replace(DADOS, classificacao=Classificacao.INACESSIVEL, obstaculos=("degrau",)), self.administrador
        )

        ultimo = TrechoService.historico(trecho.pk).first()
        self.assertEqual(ultimo.classificacao_anterior, Classificacao.PARCIAL)
        self.assertEqual(ultimo.classificacao_nova, Classificacao.INACESSIVEL)
        self.assertEqual(ultimo.alterado_por, self.administrador)
        trecho.refresh_from_db()
        self.assertEqual(list(trecho.obstaculos.values_list("codigo", flat=True)), ["degrau"])

    def test_alterar_classificacao_muda_so_classificacao_e_obstaculos(self):
        trecho = TrechoService.criar(DADOS, self.administrador)

        TrechoService.alterar_classificacao(trecho.pk, Classificacao.ACESSIVEL, self.administrador, obstaculo_codigos=[])

        trecho.refresh_from_db()
        self.assertEqual(trecho.classificacao, Classificacao.ACESSIVEL)
        self.assertFalse(trecho.obstaculos.exists())
        self.assertEqual(trecho.observacoes, DADOS.observacoes)

    def test_desativar_mantem_no_banco_e_tira_do_mapa(self):
        trecho = TrechoService.criar(DADOS, self.administrador)

        TrechoService.desativar(trecho.pk, self.administrador)

        self.assertTrue(Trecho.objects.filter(pk=trecho.pk, ativo=False).exists())
        self.assertFalse(TrechoMapa.objects.filter(pk=trecho.pk).exists())

        TrechoService.reativar(trecho.pk, self.administrador)
        self.assertTrue(TrechoMapa.objects.filter(pk=trecho.pk).exists())


class ListarParaGestaoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.jatiuca = Bairro.objects.get(nome="Jatiúca")
        for numero in range(12):
            criar_trecho(logradouro=f"Rua Centro {numero:02d}")
        criar_trecho(logradouro="Rua das Acácias", bairro=cls.jatiuca, classificacao=Classificacao.ACESSIVEL)
        antigo = criar_trecho(logradouro="Rua Antiga", ativo=False)
        Trecho.objects.filter(pk=antigo.pk).update(atualizado_em=timezone.now() - timedelta(days=200))

    def test_pagina_de_10_em_10_e_inclui_inativos(self):
        primeira = TrechoService.listar_para_gestao()
        segunda = TrechoService.listar_para_gestao(pagina=2)

        self.assertEqual(primeira.paginator.count, 14)
        self.assertEqual(len(primeira.object_list), 10)
        self.assertEqual(len(segunda.object_list), 4)
        self.assertEqual(primeira.object_list[0].logradouro, "Rua Antiga")  # ordem por logradouro

    def test_filtra_por_texto_bairro_classificacao_e_desatualizados(self):
        def logradouros(**filtros):
            return [t.logradouro for t in TrechoService.listar_para_gestao(**filtros)]

        self.assertEqual(logradouros(texto="acácias"), ["Rua das Acácias"])
        self.assertEqual(logradouros(bairro_id=self.jatiuca.pk), ["Rua das Acácias"])
        self.assertEqual(logradouros(classificacao=Classificacao.ACESSIVEL), ["Rua das Acácias"])
        self.assertEqual(logradouros(desatualizados=True), ["Rua Antiga"])
