from django.shortcuts import render
from django.views import View


class MapaView(View):
    """PROVISÓRIA: só existe para as specs 0002 a 0004 terem para onde redirecionar.

    A spec 0005 substitui esta view pelo mapa de verdade.
    """

    def get(self, request):
        return render(request, "trechos/mapa.html")
