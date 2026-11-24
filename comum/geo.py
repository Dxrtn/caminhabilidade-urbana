import math
from decimal import Decimal

RAIO_DA_TERRA_EM_METROS = 6_371_000

Coordenada = float | Decimal


def distancia_em_metros(lat1: Coordenada, lng1: Coordenada, lat2: Coordenada, lng2: Coordenada) -> float:
    """Distância entre dois pontos pela fórmula de Haversine, em metros."""
    fi1 = math.radians(float(lat1))
    fi2 = math.radians(float(lat2))
    delta_fi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lng2) - float(lng1))

    a = math.sin(delta_fi / 2) ** 2 + math.cos(fi1) * math.cos(fi2) * math.sin(delta_lambda / 2) ** 2
    return 2 * RAIO_DA_TERRA_EM_METROS * math.asin(math.sqrt(a))
