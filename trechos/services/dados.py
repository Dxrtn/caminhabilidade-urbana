from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from trechos.models import Classificacao, Obstaculo, Trecho


@dataclass(frozen=True)
class DadosTrecho:
    """Dados de entrada de um trecho. Imutável: depois de criado, não muda."""

    logradouro: str
    bairro: str  # nome do bairro
    referencia_inicio: str
    referencia_fim: str
    lado: str
    lat_inicio: Decimal
    lng_inicio: Decimal
    lat_fim: Decimal
    lng_fim: Decimal
    classificacao: str = Classificacao.SEM_AVALIACAO
    obstaculos: tuple[str, ...] = ()  # códigos dos obstáculos
    observacoes: str = ""


@dataclass(frozen=True)
class FotoPublica:
    url: str
    descricao: str  # texto alternativo


@dataclass(frozen=True)
class Relato:
    """Feedback como aparece em público: sem o autor."""

    tipo_rotulo: str
    descricao: str
    data: datetime
    em_analise: bool
    fotos: list[FotoPublica]


@dataclass(frozen=True)
class DetalheTrecho:
    trecho: Trecho
    obstaculos: list[Obstaculo]
    fotos: list[FotoPublica]
    relatos: list[Relato]
    desatualizado: bool
