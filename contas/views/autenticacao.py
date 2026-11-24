from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from contas.forms import EntrarForm


class EntrarView(View):
    template_name = "contas/entrar.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("trechos:mapa")
        contexto = {"form": EntrarForm(request), "next": request.GET.get("next", "")}
        return render(request, self.template_name, contexto)

    def post(self, request):
        form = EntrarForm(request, data=request.POST)
        destino = request.POST.get("next", "")
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "next": destino})

        login(request, form.get_user())
        if url_has_allowed_host_and_scheme(
            destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return redirect(destino)
        return redirect("trechos:mapa")


class SairView(LoginRequiredMixin, View):
    # Só POST: um GET responde 405, para que um link ou imagem não encerre a sessão.
    def post(self, request):
        logout(request)
        return redirect("trechos:mapa")
