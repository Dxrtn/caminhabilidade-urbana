from django import forms
from django.contrib.auth.forms import AuthenticationForm


class EntrarForm(AuthenticationForm):
    """Login por e-mail. A mensagem de erro padrão não revela se o e-mail existe."""

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "E-mail ou senha incorretos, ou a conta ainda não foi verificada.",
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields["username"].label = "E-mail"
        self.fields["username"].widget = forms.EmailInput(
            attrs={"autocomplete": "email", "autofocus": True, "maxlength": 200}
        )
        self.fields["password"].label = "Senha"

    def clean_username(self) -> str:
        # O cadastro guarda o e-mail em minúsculas (CadastroService).
        return self.cleaned_data["username"].strip().lower()
