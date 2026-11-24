"""Gera banco/schema.sql com o SQL de todas as migrações (spec 0008).

O arquivo é a documentação exata do que as migrações criam no PostgreSQL; não é executado.
"""

import re
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db.migrations.loader import MigrationLoader
from django.utils import timezone

APPS = ("contas", "trechos", "feedbacks")

# Contagens exibidas no fim, para conferência rápida.
PADROES = {
    "CREATE TABLE": r"\bCREATE TABLE\b",
    "CHECK": r"\bCHECK\b",
    "CREATE INDEX (inclui UNIQUE)": r"\bCREATE (?:UNIQUE )?INDEX\b",
    "CREATE TRIGGER": r"\bCREATE (?:OR REPLACE )?TRIGGER\b",
    "CREATE VIEW": r"\bCREATE (?:OR REPLACE )?VIEW\b",
}


class Command(BaseCommand):
    help = "Exporta para banco/schema.sql o SQL de todas as migrações de contas, trechos e feedbacks."

    def add_arguments(self, parser):
        parser.add_argument(
            "--saida",
            default=str(Path(settings.BASE_DIR) / "banco" / "schema.sql"),
            help="Arquivo de saída (padrão: banco/schema.sql).",
        )

    def handle(self, *args, **opcoes):
        saida = Path(opcoes["saida"])
        partes = [self._cabecalho()]
        for app, nome in self._migracoes_em_ordem():
            sql = StringIO()
            call_command("sqlmigrate", app, nome, stdout=sql, no_color=True)
            partes.append(f"-- {'=' * 77}\n-- Migração: {app}.{nome}\n-- {'=' * 77}\n{sql.getvalue().strip()}\n")

        conteudo = "\n".join(partes)
        saida.parent.mkdir(parents=True, exist_ok=True)
        saida.write_text(conteudo, encoding="utf-8")

        self.stdout.write(f"Gerado: {saida}")
        for rotulo, padrao in PADROES.items():
            self.stdout.write(f"  {rotulo}: {len(re.findall(padrao, conteudo))}")

    @staticmethod
    def _migracoes_em_ordem() -> list[tuple[str, str]]:
        """Migrações app por app (contas, trechos, feedbacks), cada app na ordem do grafo de dependências.

        Essa ordem também respeita as dependências entre apps: feedbacks depende de trechos e de
        contas, e trechos depende de contas, nunca o contrário.
        """
        grafo = MigrationLoader(None, ignore_no_migrations=True).graph
        ordem: list[tuple[str, str]] = []
        for app in APPS:
            for folha in grafo.leaf_nodes(app):
                for no in grafo.forwards_plan(folha):
                    if no[0] == app and no not in ordem:
                        ordem.append(no)
        return ordem

    @staticmethod
    def _cabecalho() -> str:
        gerado_em = timezone.localtime().strftime("%d/%m/%Y %H:%M")
        return (
            "-- =============================================================================\n"
            "-- Sistema de Mapeamento de Caminhabilidade Urbana\n"
            "-- schema.sql — SQL de todas as migrações (contas, trechos e feedbacks)\n"
            "--\n"
            f"-- Gerado em {gerado_em} pelo comando: python manage.py exportar_sql\n"
            "-- Banco: PostgreSQL. Não execute este arquivo: as estruturas são criadas por\n"
            "-- python manage.py migrate. Ele documenta exatamente o SQL que as migrações geram.\n"
            "-- =============================================================================\n"
        )
