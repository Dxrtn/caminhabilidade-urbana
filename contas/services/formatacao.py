"""Formatação de celulares para exibição. O banco guarda só os 11 dígitos."""


def formatar_celular(celular: str) -> str:
    """82999999999 -> (82) 99999-9999"""
    return f"({celular[:2]}) {celular[2:7]}-{celular[7:]}"


def mascarar_celular(celular: str) -> str:
    """82999999999 -> (82) 9****-9999"""
    return f"({celular[:2]}) {celular[2]}****-{celular[7:]}"
