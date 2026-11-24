from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class AdministradorRequeridoMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Exige login e is_staff.

    Visitante vai para a página de login (LoginRequiredMixin). Usuário autenticado
    sem is_staff recebe 403, pois o AccessMixin do Django nega com PermissionDenied
    quem já está autenticado.
    """

    def test_func(self) -> bool:
        return self.request.user.is_staff
