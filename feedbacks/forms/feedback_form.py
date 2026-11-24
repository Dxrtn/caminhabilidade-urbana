from django import forms

from comum.forms import CampoDeVariasImagens
from feedbacks.models import TipoFeedback
from feedbacks.models.escolhas import CLASSIFICACOES_SUGERIVEIS
from trechos.models import Classificacao, Obstaculo


class FeedbackForm(forms.Form):
    """Valida só o formato. "Novo problema exige obstáculo e foto" e o limite de fotos ficam no FeedbackService."""

    tipo = forms.ChoiceField(label="O que você quer relatar?", choices=TipoFeedback.choices, widget=forms.RadioSelect)
    obstaculos = forms.ModelMultipleChoiceField(
        label="Obstáculos",
        queryset=Obstaculo.objects.order_by("nome"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    classificacao_sugerida = forms.ChoiceField(
        label="Como você classificaria o trecho? (opcional)",
        required=False,
        choices=[("", "Prefiro não sugerir")] + [(valor, Classificacao(valor).label) for valor in CLASSIFICACOES_SUGERIVEIS],
    )
    descricao = forms.CharField(
        label="Descrição",
        min_length=10,
        max_length=500,
        help_text="De 10 a 500 caracteres.",
        widget=forms.Textarea(attrs={"rows": 4, "data-contador": "true"}),
    )
    fotos = CampoDeVariasImagens(
        label="Fotos",
        required=False,
        help_text="Até 3 imagens, de até 5 MB cada. Obrigatória para novo problema.",
        atributos={"capture": "environment"},  # abre a câmera no celular
    )
    # Preenchidos pelo JavaScript só se o usuário permitir a localização. Não são guardados.
    latitude = forms.FloatField(required=False, min_value=-90, max_value=90, widget=forms.HiddenInput)
    longitude = forms.FloatField(required=False, min_value=-180, max_value=180, widget=forms.HiddenInput)
