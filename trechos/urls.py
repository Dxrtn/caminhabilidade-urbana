from django.urls import path

from trechos.views import (
    BuscaApiView,
    MapaView,
    PainelView,
    TrechoCreateView,
    TrechoDesativarView,
    TrechoDetalheView,
    TrechoGestaoListView,
    TrechoReativarView,
    TrechosApiView,
    TrechoUpdateView,
)

app_name = "trechos"

urlpatterns = [
    path("", MapaView.as_view(), name="mapa"),
    path("api/trechos/", TrechosApiView.as_view(), name="api_trechos"),
    path("api/busca/", BuscaApiView.as_view(), name="api_busca"),
    path("trechos/<int:trecho_id>/", TrechoDetalheView.as_view(), name="detalhe"),
    path("painel/", PainelView.as_view(), name="painel"),
    path("painel/trechos/", TrechoGestaoListView.as_view(), name="gestao"),
    path("painel/trechos/novo/", TrechoCreateView.as_view(), name="criar"),
    path("painel/trechos/<int:trecho_id>/editar/", TrechoUpdateView.as_view(), name="editar"),
    path("painel/trechos/<int:trecho_id>/desativar/", TrechoDesativarView.as_view(), name="desativar"),
    path("painel/trechos/<int:trecho_id>/reativar/", TrechoReativarView.as_view(), name="reativar"),
]
