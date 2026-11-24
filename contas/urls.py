from django.urls import path

from contas.views import (
    CadastroView,
    EntrarView,
    ReenviarCodigoView,
    SairView,
    VerificarCelularView,
)

app_name = "contas"

urlpatterns = [
    path("cadastro/", CadastroView.as_view(), name="cadastro"),
    path("cadastro/verificar/", VerificarCelularView.as_view(), name="verificar"),
    path("cadastro/reenviar/", ReenviarCodigoView.as_view(), name="reenviar"),
    path("entrar/", EntrarView.as_view(), name="entrar"),
    path("sair/", SairView.as_view(), name="sair"),
]
