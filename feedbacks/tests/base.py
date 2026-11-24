"""Base dos testes que gravam imagens: MEDIA_ROOT temporário, apagado ao fim da classe."""

import shutil
import tempfile
from io import BytesIO

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image


def imagem_de_teste(nome: str = "calcada.png") -> SimpleUploadedFile:
    """PNG pequeno gerado pelo Pillow em memória."""
    conteudo = BytesIO()
    Image.new("RGB", (8, 8), "gray").save(conteudo, format="PNG")
    return SimpleUploadedFile(nome, conteudo.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="caminhabilidade-testes-"))
class TesteComMidia(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()
