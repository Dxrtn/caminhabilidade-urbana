from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.views import View

from comum.mixins import AdministradorRequeridoMixin
from trechos.exceptions import DadosDeTrechoInvalidos, TrechoDuplicado, TrechoNaoEncontrado
from trechos.forms import FiltroGestaoForm, TrechoForm
from trechos.services import TrechoService


class PainelView(AdministradorRequeridoMixin, View):
    def get(self, request):
        # Exceção de dependência trechos -> feedbacks (docs/arquitetura.md): import aqui dentro
        # para evitar import circular, já que feedbacks importa de trechos.
        from feedbacks.services import AnaliseService

        return render(request, "trechos/painel/inicio.html", {"em_analise": AnaliseService.contar_em_analise()})


class TrechoGestaoListView(AdministradorRequeridoMixin, View):
    def get(self, request):
        filtros = FiltroGestaoForm(request.GET)
        dados = filtros.cleaned_data if filtros.is_valid() else {}
        bairro = dados.get("bairro")
        pagina = TrechoService.listar_para_gestao(
            texto=dados.get("texto"),
            bairro_id=bairro.pk if bairro else None,
            classificacao=dados.get("classificacao"),
            desatualizados=dados.get("desatualizados", False),
            pagina=request.GET.get("pagina"),
        )
        # Mantém os filtros nos links de paginação.
        parametros = request.GET.copy()
        parametros.pop("pagina", None)
        contexto = {"filtros": filtros, "pagina": pagina, "parametros": parametros.urlencode()}
        return render(request, "trechos/painel/lista.html", contexto)


class TrechoCreateView(AdministradorRequeridoMixin, View):
    template_name = "trechos/painel/formulario.html"

    def get(self, request):
        return render(request, self.template_name, {"form": TrechoForm()})

    def post(self, request):
        form = TrechoForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})
        try:
            TrechoService.criar(form.para_dados(), request.user, fotos=form.cleaned_data["fotos"])
        except (TrechoDuplicado, DadosDeTrechoInvalidos) as exc:
            form.add_error(None, str(exc))
            return render(request, self.template_name, {"form": form})
        messages.success(request, "Trecho salvo.")
        return redirect("trechos:gestao")


class TrechoUpdateView(AdministradorRequeridoMixin, View):
    template_name = "trechos/painel/formulario.html"

    def get(self, request, trecho_id):
        trecho = _obter_ou_404(trecho_id)
        return self._exibir(request, TrechoForm(initial=TrechoForm.inicial_de(trecho)), trecho)

    def post(self, request, trecho_id):
        trecho = _obter_ou_404(trecho_id)
        form = TrechoForm(request.POST, request.FILES)
        if not form.is_valid():
            return self._exibir(request, form, trecho)
        try:
            TrechoService.atualizar(trecho_id, form.para_dados(), request.user, novas_fotos=form.cleaned_data["fotos"])
        except TrechoNaoEncontrado as exc:
            raise Http404 from exc
        except (TrechoDuplicado, DadosDeTrechoInvalidos) as exc:
            form.add_error(None, str(exc))
            return self._exibir(request, form, trecho)
        messages.success(request, "Trecho salvo.")
        return redirect("trechos:gestao")

    def _exibir(self, request, form, trecho):
        contexto = {"form": form, "trecho": trecho, "historico": TrechoService.historico(trecho.pk)}
        return render(request, self.template_name, contexto)


class TrechoDesativarView(AdministradorRequeridoMixin, View):
    def post(self, request, trecho_id):
        try:
            trecho = TrechoService.desativar(trecho_id, request.user)
        except TrechoNaoEncontrado as exc:
            raise Http404 from exc
        messages.success(request, f"Trecho desativado: {trecho}.")
        return redirect("trechos:gestao")


class TrechoReativarView(AdministradorRequeridoMixin, View):
    def post(self, request, trecho_id):
        try:
            trecho = TrechoService.reativar(trecho_id, request.user)
        except TrechoNaoEncontrado as exc:
            raise Http404 from exc
        messages.success(request, f"Trecho reativado: {trecho}.")
        return redirect("trechos:gestao")


def _obter_ou_404(trecho_id: int):
    try:
        return TrechoService.obter(trecho_id)
    except TrechoNaoEncontrado as exc:
        raise Http404 from exc
