"""Carga de trechos em lote (Template Method).

ImportadorDeTrechos.importar() é o algoritmo comum; cada subclasse só diz de onde
vêm os dados, implementando ler().
"""

import csv
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.db import IntegrityError, transaction

from trechos.exceptions import DadosDeTrechoInvalidos, TrechoDuplicado
from trechos.services.dados import DadosTrecho
from trechos.services.trecho_service import TrechoService

CABECALHO_CSV = [
    "logradouro",
    "bairro",
    "referencia_inicio",
    "referencia_fim",
    "lado",
    "lat_inicio",
    "lng_inicio",
    "lat_fim",
    "lng_fim",
    "classificacao",
    "obstaculos",
    "observacoes",
]


@dataclass
class ResultadoImportacao:
    importados: int = 0
    ignorados: int = 0  # já existiam
    erros: list[str] = field(default_factory=list)  # "linha 3: Bairro 'X' não existe."


class ImportadorDeTrechos(ABC):
    def __init__(self, administrador):
        self._administrador = administrador
        self._resultado = ResultadoImportacao()

    @abstractmethod
    def ler(self) -> Iterable[DadosTrecho]:
        """Cada subclasse devolve os dados da sua origem."""

    def importar(self) -> ResultadoImportacao:
        """Algoritmo comum: para cada item, cria pelo TrechoService e contabiliza."""
        self._resultado = ResultadoImportacao()
        for indice, dados in enumerate(self.ler(), start=1):
            try:
                with transaction.atomic():  # cada item na sua própria transação
                    TrechoService.criar(dados, self._administrador)
            except TrechoDuplicado:
                self._resultado.ignorados += 1
            except DadosDeTrechoInvalidos as exc:
                self._registrar_erro(f"{self._posicao(indice)}: {exc}")
            except IntegrityError as exc:
                self._registrar_erro(f"{self._posicao(indice)}: {self._regra_violada(exc)}")
            else:
                self._resultado.importados += 1
        return self._resultado

    def _posicao(self, indice: int) -> str:
        """Como o item aparece nas mensagens de erro. Subclasses podem trocar."""
        return f"item {indice}"

    def _registrar_erro(self, mensagem: str) -> None:
        self._resultado.erros.append(mensagem)

    @staticmethod
    def _regra_violada(exc: IntegrityError) -> str:
        restricao = getattr(getattr(exc.__cause__, "diag", None), "constraint_name", None)
        return f"o banco recusou o trecho (regra {restricao})." if restricao else "o banco recusou o trecho."


class ImportadorDadosExemplo(ImportadorDeTrechos):
    """Lê a lista TRECHOS_EXEMPLO de trechos/dados_exemplo.py."""

    def ler(self) -> Iterable[DadosTrecho]:
        from trechos.dados_exemplo import TRECHOS_EXEMPLO

        return TRECHOS_EXEMPLO


class ImportadorCsv(ImportadorDeTrechos):
    """Lê um CSV em UTF-8, separado por ';', com o cabeçalho CABECALHO_CSV."""

    def __init__(self, administrador, caminho: str | Path):
        super().__init__(administrador)
        self._caminho = Path(caminho)
        self._linha = 1

    def ler(self) -> Iterator[DadosTrecho]:
        with self._caminho.open(encoding="utf-8-sig", newline="") as arquivo:
            leitor = csv.DictReader(arquivo, delimiter=";")
            faltando = set(CABECALHO_CSV) - set(leitor.fieldnames or [])
            if faltando:
                self._registrar_erro(f"cabeçalho: faltam as colunas {', '.join(sorted(faltando))}.")
                return
            for linha in leitor:
                self._linha = leitor.line_num
                try:
                    yield self._converter(linha)
                except (InvalidOperation, ValueError) as exc:
                    self._registrar_erro(f"linha {self._linha}: {exc}")

    def _posicao(self, indice: int) -> str:
        return f"linha {self._linha}"

    @staticmethod
    def _converter(linha: dict[str, str]) -> DadosTrecho:
        def decimal(coluna: str) -> Decimal:
            valor = (linha[coluna] or "").strip().replace(",", ".")
            try:
                return Decimal(valor)
            except InvalidOperation:
                raise ValueError(f"{coluna} '{valor}' não é um número.") from None

        obstaculos = tuple(c.strip() for c in (linha["obstaculos"] or "").split(",") if c.strip())
        return DadosTrecho(
            logradouro=linha["logradouro"].strip(),
            bairro=linha["bairro"].strip(),
            referencia_inicio=linha["referencia_inicio"].strip(),
            referencia_fim=linha["referencia_fim"].strip(),
            lado=linha["lado"].strip().upper(),
            lat_inicio=decimal("lat_inicio"),
            lng_inicio=decimal("lng_inicio"),
            lat_fim=decimal("lat_fim"),
            lng_fim=decimal("lng_fim"),
            classificacao=(linha["classificacao"] or "SEM_AVALIACAO").strip().upper(),
            obstaculos=obstaculos,
            observacoes=(linha["observacoes"] or "").strip(),
        )
