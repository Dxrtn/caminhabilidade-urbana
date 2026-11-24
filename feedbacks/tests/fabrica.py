"""Dados de teste de feedbacks, usados também pelos testes do detalhe do trecho."""

from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image

from feedbacks.models import Feedback, FotoFeedback, StatusFeedback, TipoFeedback


def criar_feedback(usuario, trecho, **campos) -> Feedback:
    padrao = {"tipo": TipoFeedback.NOVO_PROBLEMA, "descricao": "Há um buraco grande no meio da calçada."}
    if campos.get("status") in (StatusFeedback.ACEITO, StatusFeedback.REJEITADO):
        padrao["analisado_em"] = timezone.now()
    return Feedback.objects.create(usuario=usuario, trecho=trecho, **{**padrao, **campos})


def criar_foto(feedback, aprovada: bool) -> FotoFeedback:
    conteudo = BytesIO()
    Image.new("RGB", (4, 4), "gray").save(conteudo, format="PNG")
    imagem = SimpleUploadedFile("relato.png", conteudo.getvalue(), content_type="image/png")
    return FotoFeedback.objects.create(feedback=feedback, imagem=imagem, aprovada=aprovada)
