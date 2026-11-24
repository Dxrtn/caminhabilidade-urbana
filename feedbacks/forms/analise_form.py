from django import forms

from feedbacks.models import MotivoRejeicao, TipoFeedback
from trechos.models import Bairro, Classificacao, Obstaculo


class AceitarFeedbackForm(forms.Form):
    nova_classificacao = forms.ChoiceField(
        label="Classificação do trecho",
        required=False,
        choices=[("", "Manter a atual")] + list(Classificacao.choices),
        help_text="Ao escolher uma classificação, os obstáculos marcados abaixo passam a ser os do trecho.",
    )
    obstaculos = forms.ModelMultipleChoiceField(
        label="Obstáculos do trecho",
        queryset=Obstaculo.objects.order_by("nome"),
        to_field_name="codigo",
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    fotos_aprovadas = forms.ModelMultipleChoiceField(
        label="Fotos que ficam públicas",
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Não aprove fotos em que apareçam rostos ou placas de veículos.",
    )

    def __init__(self, *args, feedback, **kwargs):
        super().__init__(*args, **kwargs)
        # Só as fotos deste feedback podem ser escolhidas.
        self.fields["fotos_aprovadas"].queryset = feedback.fotos.order_by("criado_em", "id")
        if not self.is_bound:
            self.initial["obstaculos"] = [obstaculo.codigo for obstaculo in feedback.obstaculos.all()]

    def obstaculos_para_o_trecho(self) -> list[str] | None:
        """Códigos a gravar no trecho, ou None para não mexer nos obstáculos dele."""
        if not self.cleaned_data["nova_classificacao"]:
            return None
        return [obstaculo.codigo for obstaculo in self.cleaned_data["obstaculos"]]


class RejeitarFeedbackForm(forms.Form):
    """O texto obrigatório para "Outro" é regra de negócio: fica no AnaliseService."""

    motivo = forms.ChoiceField(label="Motivo", choices=MotivoRejeicao.choices, widget=forms.RadioSelect)
    texto = forms.CharField(
        label="Detalhes",
        max_length=300,
        required=False,
        help_text="Obrigatório quando o motivo é \"Outro\". O usuário verá este texto.",
        widget=forms.Textarea(attrs={"rows": 2}),
    )


class FiltroFilaForm(forms.Form):
    bairro = forms.ModelChoiceField(queryset=Bairro.objects.all(), required=False, empty_label="Todos os bairros")
    tipo = forms.ChoiceField(label="Tipo", required=False, choices=[("", "Todos os tipos")] + list(TipoFeedback.choices))
