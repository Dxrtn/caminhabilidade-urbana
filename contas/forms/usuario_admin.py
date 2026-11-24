from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from contas.models import Usuario


class UsuarioCriacaoAdminForm(AdminUserCreationForm):
    """Formulário de criação do Admin ajustado ao Usuario, que não tem username."""

    class Meta:
        model = Usuario
        fields = ("email", "nome_completo", "celular", "locomocao")


class UsuarioAlteracaoAdminForm(UserChangeForm):
    class Meta:
        model = Usuario
        fields = (
            "email",
            "password",
            "nome_completo",
            "celular",
            "locomocao",
            "celular_verificado",
            "termos_aceitos_em",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
            "last_login",
            "date_joined",
        )
