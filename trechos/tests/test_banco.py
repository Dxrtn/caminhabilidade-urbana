"""Testes das estruturas de banco de trechos: dados de referência, constraints, trigger e ON DELETE."""

import shutil
import tempfile
from decimal import Decimal

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, connection, transaction
from django.test import TestCase, override_settings

from trechos.models import (
    Bairro,
    Classificacao,
    FotoTrecho,
    HistoricoTrecho,
    Obstaculo,
    Trecho,
    TrechoObstaculo,
)
from trechos.tests.fabrica import criar_trecho, criar_usuario, dados_de_trecho


class DadosDeReferenciaTests(TestCase):
    def test_migracao_cria_os_12_obstaculos_e_os_bairros(self):
        self.assertEqual(Obstaculo.objects.count(), 12)
        self.assertTrue(Obstaculo.objects.filter(codigo="rampa-ausente", nome="Rampa ausente").exists())
        self.assertEqual(Bairro.objects.count(), 49)
        self.assertTrue(Bairro.objects.filter(nome="Jatiúca").exists())


class TrechoConstraintsTests(TestCase):
    def _assert_banco_rejeita(self, **campos):
        with self.assertRaises(IntegrityError), transaction.atomic():
            criar_trecho(**campos)

    def test_banco_rejeita_classificacao_invalida(self):
        self._assert_banco_rejeita(classificacao="OTIMA")

    def test_banco_rejeita_coordenada_fora_de_maceio(self):
        self._assert_banco_rejeita(lat_fim=Decimal("-23.550500"))  # São Paulo

    def test_banco_rejeita_inicio_igual_ao_fim(self):
        self._assert_banco_rejeita(lat_fim=Decimal("-9.665800"), lng_fim=Decimal("-35.735300"))

    def test_banco_rejeita_trecho_duplicado(self):
        dados = dados_de_trecho()
        Trecho.objects.create(**dados)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Trecho.objects.create(**{**dados, "lat_inicio": Decimal("-9.660000")})


class TriggerHistoricoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.administrador = criar_usuario(is_staff=True)

    def test_grava_historico_ao_criar_e_ao_mudar_a_classificacao(self):
        trecho = criar_trecho(atualizado_por=self.administrador)

        trecho.classificacao = Classificacao.INACESSIVEL
        trecho.save()

        historico = list(HistoricoTrecho.objects.filter(trecho=trecho))
        self.assertEqual(len(historico), 2)
        criacao, mudanca = historico
        self.assertIsNone(criacao.classificacao_anterior)
        self.assertEqual(criacao.classificacao_nova, Classificacao.SEM_AVALIACAO)
        self.assertEqual(mudanca.classificacao_anterior, Classificacao.SEM_AVALIACAO)
        self.assertEqual(mudanca.classificacao_nova, Classificacao.INACESSIVEL)
        self.assertEqual(mudanca.alterado_por, self.administrador)
        self.assertIsNotNone(mudanca.alterado_em)

    def test_nao_grava_historico_quando_so_outro_campo_muda(self):
        trecho = criar_trecho()

        # O save() do Django inclui a classificação no UPDATE; a trigger compara os valores.
        trecho.observacoes = "Calçada estreita."
        trecho.save()

        self.assertEqual(HistoricoTrecho.objects.filter(trecho=trecho).count(), 1)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="caminhabilidade-testes-"))
class ExclusaoDeTrechoNoBancoTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def _excluir_no_banco(self, trecho_id: int) -> None:
        with connection.cursor() as cursor:
            # As FKs do Django são DEFERRABLE; aqui a verificação precisa ser imediata.
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            cursor.execute("DELETE FROM trecho WHERE id = %s", [trecho_id])

    def test_excluir_trecho_apaga_fotos_obstaculos_e_historico(self):
        trecho = criar_trecho()
        TrechoObstaculo.objects.create(trecho=trecho, obstaculo=Obstaculo.objects.get(codigo="buraco"))
        FotoTrecho.objects.create(
            trecho=trecho, imagem=SimpleUploadedFile("foto.jpg", b"x", content_type="image/jpeg")
        )

        self._excluir_no_banco(trecho.pk)

        self.assertFalse(TrechoObstaculo.objects.filter(trecho_id=trecho.pk).exists())
        self.assertFalse(FotoTrecho.objects.filter(trecho_id=trecho.pk).exists())
        self.assertFalse(HistoricoTrecho.objects.filter(trecho_id=trecho.pk).exists())
