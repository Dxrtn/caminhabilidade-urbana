import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase


class ExportarSqlTests(TestCase):
    def test_gera_arquivo_com_trigger_view_indice_e_check(self):
        with tempfile.TemporaryDirectory() as pasta:
            saida = Path(pasta) / "schema.sql"
            relatorio = StringIO()

            call_command("exportar_sql", saida=str(saida), stdout=relatorio)

            sql = saida.read_text(encoding="utf-8")
        self.assertIn("CREATE TRIGGER trg_trecho_historico", sql)
        self.assertIn("CREATE OR REPLACE VIEW vw_trechos_mapa", sql)
        self.assertIn('CREATE INDEX "idx_feedback_status_criado"', sql)
        self.assertIn("CHECK", sql)
        self.assertIn("-- Migração: contas.0001_initial", sql)
        self.assertLess(sql.index("-- Migração: trechos.0001_initial"), sql.index("-- Migração: feedbacks.0001_initial"))
        self.assertIn("CREATE TRIGGER: 1", relatorio.getvalue())
