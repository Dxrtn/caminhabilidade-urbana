from django.urls import path

from trechos.views import (
    MapaView,
    PainelView,
    TrechoCreateView,
    TrechoDesativarView,
    TrechoGestaoListView,
    TrechoReativarView,
    TrechoUpdateView,
)

app_name = "trechos"

urlpatterns = [
    path("", MapaView.as_view(), name="mapa"),  # provisória até a spec 0005
    path("painel/", PainelView.as_view(), name="painel"),
    path("painel/trechos/", TrechoGestaoListView.as_view(), name="gestao"),
    path("painel/trechos/novo/", TrechoCreateView.as_view(), name="criar"),
    path("painel/trechos/<int:trecho_id>/editar/", TrechoUpdateView.as_view(), name="editar"),
    path("painel/trechos/<int:trecho_id>/desativar/", TrechoDesativarView.as_view(), name="desativar"),
    path("painel/trechos/<int:trecho_id>/reativar/", TrechoReativarView.as_view(), name="reativar"),
]
