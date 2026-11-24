from django import forms

from trechos.models import Bairro, Classificacao, Lado, Obstaculo
from trechos.models.escolhas import LATITUDE_MAXIMA, LATITUDE_MINIMA, LONGITUDE_MAXIMA, LONGITUDE_MINIMA
from trechos.services.dados import DadosTrecho

MAXIMO_DE_FOTOS = 5
TAMANHO_MAXIMO_DA_FOTO = 5 * 1024 * 1024  # 5 MB


class EntradaDeVariosArquivos(forms.ClearableFileInput):
    allow_multiple_selected = True


class CampoDeVariasImagens(forms.ImageField):
    """Aceita várias imagens no mesmo campo; cada uma é validada pelo ImageField (Pillow)."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", EntradaDeVariosArquivos(attrs={"accept": "image/*"}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        arquivos = data if isinstance(data, (list, tuple)) else [data]
        arquivos = [arquivo for arquivo in arquivos if arquivo]
        if len(arquivos) > MAXIMO_DE_FOTOS:
            raise forms.ValidationError(f"Envie no máximo {MAXIMO_DE_FOTOS} fotos.")
        for arquivo in arquivos:
            if arquivo.size > TAMANHO_MAXIMO_DA_FOTO:
                raise forms.ValidationError(f"A foto '{arquivo.name}' passa de 5 MB.")
        return [super(CampoDeVariasImagens, self).clean(arquivo, initial) for arquivo in arquivos]


def _coordenada(rotulo: str, minimo, maximo) -> forms.DecimalField:
    return forms.DecimalField(
        label=rotulo,
        max_digits=9,
        decimal_places=6,
        min_value=minimo,
        max_value=maximo,
        error_messages={
            "min_value": f"Fora de Maceió: use um valor entre {minimo} e {maximo}.",
            "max_value": f"Fora de Maceió: use um valor entre {minimo} e {maximo}.",
        },
        widget=forms.NumberInput(attrs={"step": "0.000001", "inputmode": "decimal"}),
    )


class TrechoForm(forms.Form):
    """Valida o formato. Duplicidade e bairro existente ficam com o TrechoService."""

    logradouro = forms.CharField(max_length=150)
    bairro = forms.ModelChoiceField(queryset=Bairro.objects.all(), empty_label="Escolha o bairro")
    referencia_inicio = forms.CharField(label="Referência de início", max_length=150, help_text="Ex.: Esquina com a Rua A.")
    referencia_fim = forms.CharField(label="Referência de fim", max_length=150)
    lado = forms.ChoiceField(choices=Lado.choices)
    lat_inicio = _coordenada("Latitude de início", LATITUDE_MINIMA, LATITUDE_MAXIMA)
    lng_inicio = _coordenada("Longitude de início", LONGITUDE_MINIMA, LONGITUDE_MAXIMA)
    lat_fim = _coordenada("Latitude de fim", LATITUDE_MINIMA, LATITUDE_MAXIMA)
    lng_fim = _coordenada("Longitude de fim", LONGITUDE_MINIMA, LONGITUDE_MAXIMA)
    classificacao = forms.ChoiceField(label="Classificação", choices=Classificacao.choices, initial=Classificacao.SEM_AVALIACAO)
    obstaculos = forms.ModelMultipleChoiceField(
        label="Obstáculos",
        queryset=Obstaculo.objects.all(),
        to_field_name="codigo",
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    observacoes = forms.CharField(
        label="Observações", max_length=500, required=False, widget=forms.Textarea(attrs={"rows": 3})
    )
    fotos = CampoDeVariasImagens(
        label="Fotos", required=False, help_text="Até 5 imagens, de até 5 MB cada. São públicas."
    )

    def clean(self) -> dict:
        dados = super().clean()
        inicio = (dados.get("lat_inicio"), dados.get("lng_inicio"))
        fim = (dados.get("lat_fim"), dados.get("lng_fim"))
        if None not in inicio and inicio == fim:
            raise forms.ValidationError("O início e o fim do trecho precisam ser pontos diferentes.")
        return dados

    def para_dados(self) -> DadosTrecho:
        dados = self.cleaned_data
        return DadosTrecho(
            logradouro=dados["logradouro"].strip(),
            bairro=dados["bairro"].nome,
            referencia_inicio=dados["referencia_inicio"].strip(),
            referencia_fim=dados["referencia_fim"].strip(),
            lado=dados["lado"],
            lat_inicio=dados["lat_inicio"],
            lng_inicio=dados["lng_inicio"],
            lat_fim=dados["lat_fim"],
            lng_fim=dados["lng_fim"],
            classificacao=dados["classificacao"],
            obstaculos=tuple(o.codigo for o in dados["obstaculos"]),
            observacoes=dados["observacoes"].strip(),
        )

    @staticmethod
    def inicial_de(trecho) -> dict:
        """Valores iniciais do formulário de edição."""
        return {
            "logradouro": trecho.logradouro,
            "bairro": trecho.bairro_id,
            "referencia_inicio": trecho.referencia_inicio,
            "referencia_fim": trecho.referencia_fim,
            "lado": trecho.lado,
            "lat_inicio": trecho.lat_inicio,
            "lng_inicio": trecho.lng_inicio,
            "lat_fim": trecho.lat_fim,
            "lng_fim": trecho.lng_fim,
            "classificacao": trecho.classificacao,
            "obstaculos": [o.codigo for o in trecho.obstaculos.all()],
            "observacoes": trecho.observacoes,
        }


class FiltroGestaoForm(forms.Form):
    """Filtros da lista de gestão, lidos da query string."""

    texto = forms.CharField(label="Logradouro", required=False, max_length=150)
    bairro = forms.ModelChoiceField(queryset=Bairro.objects.all(), required=False, empty_label="Todos os bairros")
    classificacao = forms.ChoiceField(
        label="Classificação", required=False, choices=[("", "Todas")] + list(Classificacao.choices)
    )
    desatualizados = forms.BooleanField(label="Sem atualização há mais de 6 meses", required=False)
