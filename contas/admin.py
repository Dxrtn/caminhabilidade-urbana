from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from contas.forms import UsuarioAlteracaoAdminForm, UsuarioCriacaoAdminForm
from contas.models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    form = UsuarioAlteracaoAdminForm
    add_form = UsuarioCriacaoAdminForm

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Dados pessoais", {"fields": ("nome_completo", "celular", "locomocao")}),
        ("Verificação", {"fields": ("celular_verificado", "termos_aceitos_em")}),
        (
            "Permissões",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Datas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "nome_completo",
                    "celular",
                    "locomocao",
                    "usable_password",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
    list_display = ("email", "nome_completo", "celular", "celular_verificado", "is_active", "is_staff")
    list_filter = ("is_staff", "is_active", "celular_verificado", "locomocao")
    search_fields = ("email", "nome_completo", "celular")
    ordering = ("email",)
