from django.urls import path

from trechos.views import MapaView

app_name = "trechos"

urlpatterns = [
    path("", MapaView.as_view(), name="mapa"),
]
