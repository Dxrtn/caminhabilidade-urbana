from django import forms

TAMANHO_MAXIMO_DA_FOTO = 5 * 1024 * 1024  # 5 MB (RNF-04)


class EntradaDeVariosArquivos(forms.ClearableFileInput):
    allow_multiple_selected = True


class CampoDeVariasImagens(forms.ImageField):
    """Aceita várias imagens no mesmo campo; cada uma é validada pelo ImageField (Pillow).

    `maximo_de_arquivos=None` deixa a contagem para quem usa o campo (ex.: o FeedbackService).
    """

    def __init__(self, *args, maximo_de_arquivos: int | None = None, atributos: dict | None = None, **kwargs):
        self.maximo_de_arquivos = maximo_de_arquivos
        kwargs.setdefault("widget", EntradaDeVariosArquivos(attrs={"accept": "image/*", **(atributos or {})}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        arquivos = data if isinstance(data, (list, tuple)) else [data]
        arquivos = [arquivo for arquivo in arquivos if arquivo]
        if self.maximo_de_arquivos is not None and len(arquivos) > self.maximo_de_arquivos:
            raise forms.ValidationError(f"Envie no máximo {self.maximo_de_arquivos} fotos.")
        for arquivo in arquivos:
            if arquivo.size > TAMANHO_MAXIMO_DA_FOTO:
                raise forms.ValidationError(f"A foto '{arquivo.name}' passa de 5 MB.")
        return [super(CampoDeVariasImagens, self).clean(arquivo, initial) for arquivo in arquivos]
