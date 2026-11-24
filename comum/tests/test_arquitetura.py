"""Garante a regra do AGENTS.md: toda view é uma classe que herda de django.views.View."""

import importlib
import inspect
import pkgutil

from django.test import SimpleTestCase
from django.urls import URLPattern, URLResolver, get_resolver
from django.views import View
from django.views.static import serve

PACOTES_DE_VIEWS = ["contas.views", "trechos.views", "feedbacks.views"]


def _modulos(nome_pacote: str):
    pacote = importlib.import_module(nome_pacote)
    yield pacote
    for info in pkgutil.walk_packages(pacote.__path__, prefix=f"{nome_pacote}."):
        yield importlib.import_module(info.name)


def _padroes(padroes, prefixo=""):
    """Percorre as rotas do projeto, pulando o Admin."""
    for padrao in padroes:
        rota = f"{prefixo}{padrao.pattern}"
        if isinstance(padrao, URLResolver):
            if padrao.app_name == "admin":
                continue
            yield from _padroes(padrao.url_patterns, rota)
        elif isinstance(padrao, URLPattern):
            yield rota, padrao


class ArquiteturaTests(SimpleTestCase):
    def test_classes_terminadas_em_view_herdam_de_view(self):
        for nome_pacote in PACOTES_DE_VIEWS:
            for modulo in _modulos(nome_pacote):
                for nome, classe in inspect.getmembers(modulo, inspect.isclass):
                    if classe.__module__ != modulo.__name__ or not nome.endswith("View"):
                        continue
                    with self.subTest(view=f"{modulo.__name__}.{nome}"):
                        self.assertTrue(
                            issubclass(classe, View),
                            f"{nome} precisa herdar de django.views.View.",
                        )

    def test_rotas_apontam_para_views_de_classe(self):
        for rota, padrao in _padroes(get_resolver().url_patterns):
            if padrao.callback is serve:
                continue  # arquivos de mídia servidos em DEBUG
            with self.subTest(rota=rota):
                self.assertTrue(
                    hasattr(padrao.callback, "view_class"),
                    f"A rota '{rota}' precisa usar uma view criada com as_view().",
                )
