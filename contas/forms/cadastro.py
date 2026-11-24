import re

from django import forms

from contas.models import Locomocao

MENSAGEM_CELULAR = "Informe o celular com DDD, ex.: (82) 99999-9999."
MENSAGEM_SENHA = "A senha precisa ter de 8 a 64 caracteres, com ao menos uma letra e um número."


class CadastroForm(forms.Form):
    """Valida só o formato. E-mail e celular repetidos são verificados pelo CadastroService."""

    nome_completo = forms.CharField(
        label="Nome completo",
        min_length=3,
        max_length=120,
        widget=forms.TextInput(attrs={"autocomplete": "name"}),
    )
    email = forms.EmailField(
        label="E-mail",
        max_length=200,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    celular = forms.CharField(
        label="Celular",
        max_length=20,
        help_text="Com DDD. Enviaremos um código por SMS.",
        widget=forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"}),
    )
    senha = forms.CharField(
        label="Senha",
        strip=False,
        help_text="De 8 a 64 caracteres, com letras e números.",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    confirmacao_senha = forms.CharField(
        label="Confirme a senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    locomocao = forms.TypedChoiceField(
        label="Como você se locomove? (opcional)",
        choices=Locomocao.choices,
        required=False,
        empty_value=Locomocao.NAO_INFORMADO,
        initial=Locomocao.NAO_INFORMADO,
    )
    aceite_termos = forms.BooleanField(
        label="Li e aceito os termos de uso",
        error_messages={"required": "Para criar a conta, aceite os termos de uso."},
    )

    def clean_celular(self) -> str:
        digitos = re.sub(r"\D", "", self.cleaned_data["celular"])
        if len(digitos) != 11 or digitos[2] != "9":
            raise forms.ValidationError(MENSAGEM_CELULAR)
        return digitos

    def clean_senha(self) -> str:
        senha = self.cleaned_data["senha"]
        tamanho_ok = 8 <= len(senha) <= 64
        tem_letra = any(caractere.isalpha() for caractere in senha)
        tem_numero = any(caractere.isdigit() for caractere in senha)
        if not (tamanho_ok and tem_letra and tem_numero):
            raise forms.ValidationError(MENSAGEM_SENHA)
        return senha

    def clean(self) -> dict:
        dados = super().clean()
        senha = dados.get("senha")
        confirmacao = dados.get("confirmacao_senha")
        if senha and confirmacao and senha != confirmacao:
            self.add_error("confirmacao_senha", "As senhas não conferem.")
        return dados


class VerificacaoForm(forms.Form):
    codigo = forms.RegexField(
        label="Código recebido por SMS",
        regex=r"^[0-9]{6}$",
        max_length=6,
        error_messages={"invalid": "O código tem 6 números."},
        widget=forms.TextInput(
            attrs={"inputmode": "numeric", "autocomplete": "one-time-code", "pattern": "[0-9]{6}"}
        ),
    )
