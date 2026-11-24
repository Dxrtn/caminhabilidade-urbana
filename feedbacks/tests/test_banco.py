"""Testes das estruturas de banco de feedbacks: constraints, view vw_trechos_mapa e ON DELETE."""

from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from django.utils import timezone

from feedbacks.models import Feedback, MotivoRejeicao, StatusFeedback, TipoFeedback
from trechos.models import TrechoMapa
from trechos.tests.fabrica import criar_trecho, criar_usuario

DESCRICAO = "Há um buraco grande no meio da calçada."


def criar_feedback(usuario, trecho, **campos) -> Feedback:
    padrao = {"tipo": TipoFeedback.NOVO_PROBLEMA, "descricao": DESCRICAO}
    return Feedback.objects.create(usuario=usuario, trecho=trecho, **{**padrao, **campos})


class FeedbackConstraintsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = criar_usuario()
        cls.trecho = criar_trecho()

    def _assert_banco_rejeita(self, **campos):
        with self.assertRaises(IntegrityError), transaction.atomic():
            criar_feedback(self.usuario, self.trecho, **campos)

    def test_banco_rejeita_feedback_rejeitado_sem_motivo(self):
        self._assert_banco_rejeita(status=StatusFeedback.REJEITADO, analisado_em=timezone.now())

    def test_banco_rejeita_motivo_outro_sem_texto(self):
        self._assert_banco_rejeita(
            status=StatusFeedback.REJEITADO,
            analisado_em=timezone.now(),
            motivo_rejeicao=MotivoRejeicao.OUTRO,
        )

    def test_banco_aceita_motivo_outro_com_texto(self):
        feedback = criar_feedback(
            self.usuario,
            self.trecho,
            status=StatusFeedback.REJEITADO,
            analisado_em=timezone.now(),
            motivo_rejeicao=MotivoRejeicao.OUTRO,
            motivo_rejeicao_texto="Trecho errado.",
        )

        self.assertIsNotNone(feedback.pk)

    def test_banco_rejeita_feedback_aceito_sem_data_de_analise(self):
        self._assert_banco_rejeita(status=StatusFeedback.ACEITO)

    def test_banco_rejeita_descricao_com_menos_de_10_caracteres(self):
        self._assert_banco_rejeita(descricao="Buraco.")

    def test_banco_rejeita_segundo_em_analise_e_aceita_depois_da_analise(self):
        primeiro = criar_feedback(self.usuario, self.trecho)

        self._assert_banco_rejeita()

        Feedback.objects.filter(pk=primeiro.pk).update(status=StatusFeedback.ACEITO, analisado_em=timezone.now())
        segundo = criar_feedback(self.usuario, self.trecho)
        self.assertEqual(segundo.status, StatusFeedback.EM_ANALISE)


class ViewTrechosMapaTests(TestCase):
    def test_lista_so_trechos_ativos_e_conta_so_feedbacks_em_analise(self):
        ativo = criar_trecho()
        inativo = criar_trecho(ativo=False)
        criar_feedback(criar_usuario(), ativo)
        criar_feedback(criar_usuario(), ativo)
        criar_feedback(
            criar_usuario(), ativo, status=StatusFeedback.ACEITO, analisado_em=timezone.now()
        )

        ids = set(TrechoMapa.objects.values_list("id", flat=True))

        self.assertIn(ativo.pk, ids)
        self.assertNotIn(inativo.pk, ids)
        linha = TrechoMapa.objects.get(pk=ativo.pk)
        self.assertEqual(linha.feedbacks_em_analise, 2)
        self.assertEqual(linha.bairro, "Centro")
        self.assertEqual(linha.dias_sem_atualizacao, 0)


class ExclusaoDeTrechoComFeedbackTests(TestCase):
    def test_banco_bloqueia_excluir_trecho_com_feedback(self):
        trecho = criar_trecho()
        criar_feedback(criar_usuario(), trecho)

        with self.assertRaises(IntegrityError), transaction.atomic(), connection.cursor() as cursor:
            # As FKs do Django são DEFERRABLE; aqui a verificação precisa ser imediata.
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            cursor.execute("DELETE FROM trecho WHERE id = %s", [trecho.pk])
