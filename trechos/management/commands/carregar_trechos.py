from django.core.management.base import BaseCommand, CommandError

from trechos.exceptions import TrechoErro
from trechos.services import ImportadorCsv, ImportadorDadosExemplo, ImportadorDeTrechos, TrechoService


class Command(BaseCommand):
    help = "Carrega trechos em lote, da lista de exemplo ou de um CSV. Pode ser rodado de novo sem duplicar."

    def add_arguments(self, parser):
        origem = parser.add_mutually_exclusive_group(required=True)
        origem.add_argument("--exemplo", action="store_true", help="Usa trechos/dados_exemplo.py.")
        origem.add_argument("--csv", metavar="ARQUIVO", help="CSV em UTF-8, separado por ';'.")
        parser.add_argument("--admin", required=True, metavar="EMAIL", help="E-mail de um administrador.")

    def handle(self, *args, **opcoes):
        try:
            administrador = TrechoService.obter_administrador(opcoes["admin"])
        except TrechoErro as exc:
            raise CommandError(str(exc)) from exc

        importador: ImportadorDeTrechos
        if opcoes["exemplo"]:
            importador = ImportadorDadosExemplo(administrador)
        else:
            importador = ImportadorCsv(administrador, opcoes["csv"])

        try:
            # Polimorfismo: o comando não sabe de onde vêm os dados.
            resultado = importador.importar()
        except OSError as exc:
            raise CommandError(f"Não foi possível ler o arquivo: {exc}") from exc

        self.stdout.write(f"Importados: {resultado.importados}")
        self.stdout.write(f"Ignorados (já existiam): {resultado.ignorados}")
        self.stdout.write(f"Erros: {len(resultado.erros)}")
        for erro in resultado.erros:
            self.stdout.write(self.style.ERROR(f"  - {erro}"))
