"""Envio do código de verificação (ADR 0005).

Os services dependem só de EnviadorDeCodigo; a subclasse usada vem de
settings.ENVIADOR_DE_CODIGO.
"""

import logging
from abc import ABC, abstractmethod

from django.conf import settings
from django.utils.module_loading import import_string

from contas.services.formatacao import formatar_celular

logger = logging.getLogger("contas.sms")


class EnviadorDeCodigo(ABC):
    @abstractmethod
    def enviar(self, celular: str, codigo: str) -> None:
        """Entrega o código ao dono do celular."""


class EnviadorSmsSimulado(EnviadorDeCodigo):
    """Desenvolvimento: mostra o SMS no terminal, pelo logger contas.sms."""

    def enviar(self, celular: str, codigo: str) -> None:
        logger.info("[SMS SIMULADO] Para %s: seu código é %s", formatar_celular(celular), codigo)


class EnviadorEmMemoria(EnviadorDeCodigo):
    """Testes: guarda os envios para conferência."""

    enviados: list[tuple[str, str]] = []

    def enviar(self, celular: str, codigo: str) -> None:
        type(self).enviados.append((celular, codigo))

    @classmethod
    def limpar(cls) -> None:
        cls.enviados.clear()


def obter_enviador() -> EnviadorDeCodigo:
    return import_string(settings.ENVIADOR_DE_CODIGO)()
