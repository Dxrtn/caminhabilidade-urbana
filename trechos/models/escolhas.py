from decimal import Decimal

from django.db import models


class Classificacao(models.TextChoices):
    ACESSIVEL = "ACESSIVEL", "Acessível"
    PARCIAL = "PARCIAL", "Parcialmente acessível"
    INACESSIVEL = "INACESSIVEL", "Inacessível"
    SEM_AVALIACAO = "SEM_AVALIACAO", "Sem avaliação"


class Lado(models.TextChoices):
    PAR = "PAR", "Lado par"
    IMPAR = "IMPAR", "Lado ímpar"
    UNICO = "UNICO", "Lado único"


# Limites de Maceió, usados em ck_trecho_coordenadas_em_maceio.
LATITUDE_MINIMA = Decimal("-9.80")
LATITUDE_MAXIMA = Decimal("-9.30")
LONGITUDE_MINIMA = Decimal("-35.90")
LONGITUDE_MAXIMA = Decimal("-35.50")
