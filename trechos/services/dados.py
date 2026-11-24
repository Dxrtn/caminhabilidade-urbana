from dataclasses import dataclass
from decimal import Decimal

from trechos.models import Classificacao


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
