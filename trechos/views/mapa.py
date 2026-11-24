from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views import View

from trechos.exceptions import TextoDeBuscaCurto, TrechoNaoEncontrado
from trechos.models import Classificacao
from trechos.services import TrechoConsultaService


class MapaView(View):
    """Página inicial: o mapa público (RF-09 a RF-13)."""

    def get(self, request):
        contexto = {
            "classificacoes": Classificacao.choices,
            "obstaculos": TrechoConsultaService.listar_obstaculos(),
        }
        return render(request, "trechos/mapa.html", contexto)


class TrechosApiView(View):
    def get(self, request):
        trechos = TrechoConsultaService.listar_para_mapa(
            classificacao=request.GET.get("classificacao") or None,
            obstaculo_codigo=request.GET.get("obstaculo") or None,
        )
        return JsonResponse({"trechos": trechos})


class BuscaApiView(View):
    def get(self, request):
        try:
            resultados = TrechoConsultaService.buscar(request.GET.get("q", ""))
        except TextoDeBuscaCurto as exc:
            return JsonResponse({"resultados": [], "aviso": str(exc)})
        return JsonResponse({"resultados": resultados})


class TrechoDetalheView(View):
    def get(self, request, trecho_id):
        try:
            detalhe = TrechoConsultaService.obter_detalhe(trecho_id)
        except TrechoNaoEncontrado as exc:
            raise Http404 from exc
        return render(request, "trechos/detalhe.html", {"detalhe": detalhe, "trecho": detalhe.trecho})
