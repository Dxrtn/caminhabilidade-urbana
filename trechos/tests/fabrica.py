"""Dados de teste compartilhados pelos testes de trechos e feedbacks."""

from decimal import Decimal

from django.contrib.auth import get_user_model

from trechos.models import Bairro, Lado, Trecho

_contador = {"usuario": 0, "trecho": 0}


def criar_usuario(**campos):
    _contador["usuario"] += 1
    numero = _contador["usuario"]
    padrao = {
        "nome_completo": f"Usuário {numero}",
        "celular": f"829{numero:08d}",
        "celular_verificado": True,
        "is_active": True,
    }
    return get_user_model().objects.create_user(f"usuario{numero}@exemplo.com", "senhaforte1", **{**padrao, **campos})


def dados_de_trecho(**campos) -> dict:
    _contador["trecho"] += 1
    padrao = {
        "logradouro": f"Rua de Teste {_contador['trecho']}",
        "bairro": Bairro.objects.get(nome="Centro"),
        "referencia_inicio": "Esquina com a Rua A",
        "referencia_fim": "Esquina com a Rua B",
        "lado": Lado.PAR,
        "lat_inicio": Decimal("-9.665800"),
        "lng_inicio": Decimal("-35.735300"),
        "lat_fim": Decimal("-9.666500"),
        "lng_fim": Decimal("-35.736000"),
    }
    return {**padrao, **campos}


def criar_trecho(**campos) -> Trecho:
    return Trecho.objects.create(**dados_de_trecho(**campos))
