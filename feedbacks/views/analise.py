from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.views import View

from comum.mixins import AdministradorRequeridoMixin
from feedbacks.exceptions import FeedbackJaAnalisado, FeedbackNaoEncontrado, MotivoDeRejeicaoInvalido
from feedbacks.forms import AceitarFeedbackForm, FiltroFilaForm, RejeitarFeedbackForm
from feedbacks.services import AnaliseService
from trechos.exceptions import DadosDeTrechoInvalidos

TEMPLATE_ANALISAR = "feedbacks/painel/analisar.html"


class FilaAnaliseView(AdministradorRequeridoMixin, View):
    def get(self, request):
        filtros = FiltroFilaForm(request.GET)
        dados = filtros.cleaned_data if filtros.is_valid() else {}
        bairro = dados.get("bairro")
        pagina = AnaliseService.fila(
            pagina=request.GET.get("pagina"),
            bairro_id=bairro.pk if bairro else None,
            tipo=dados.get("tipo") or None,
        )
        parametros = request.GET.copy()
        parametros.pop("pagina", None)
        contexto = {"filtros": filtros, "pagina": pagina, "parametros": parametros.urlencode()}
        return render(request, "feedbacks/painel/fila.html", contexto)


class AnalisarFeedbackView(AdministradorRequeridoMixin, View):
    def get(self, request, feedback_id):
        feedback = _feedback_ou_404(feedback_id)
        return _exibir_analise(
            request, feedback, AceitarFeedbackForm(feedback=feedback), RejeitarFeedbackForm()
        )


class AceitarFeedbackView(AdministradorRequeridoMixin, View):
    def post(self, request, feedback_id):
        feedback = _feedback_ou_404(feedback_id)
        form = AceitarFeedbackForm(request.POST, feedback=feedback)
        if not form.is_valid():
            return _exibir_analise(request, feedback, form, RejeitarFeedbackForm())
        try:
            AnaliseService.aceitar(
                feedback_id,
                request.user,
                nova_classificacao=form.cleaned_data["nova_classificacao"] or None,
                obstaculo_codigos=form.obstaculos_para_o_trecho(),
                fotos_aprovadas_ids=[foto.pk for foto in form.cleaned_data["fotos_aprovadas"]],
            )
        except FeedbackNaoEncontrado as exc:
            raise Http404 from exc
        except FeedbackJaAnalisado as exc:
            messages.error(request, str(exc))
            return redirect("feedbacks:fila")
        except DadosDeTrechoInvalidos as exc:
            form.add_error(None, str(exc))
            return _exibir_analise(request, feedback, form, RejeitarFeedbackForm())
        messages.success(request, "Feedback aceito.")
        return redirect("feedbacks:fila")


class RejeitarFeedbackView(AdministradorRequeridoMixin, View):
    def post(self, request, feedback_id):
        feedback = _feedback_ou_404(feedback_id)
        form = RejeitarFeedbackForm(request.POST)
        if not form.is_valid():
            return _exibir_analise(request, feedback, AceitarFeedbackForm(feedback=feedback), form)
        try:
            AnaliseService.rejeitar(feedback_id, request.user, form.cleaned_data["motivo"], form.cleaned_data["texto"])
        except FeedbackNaoEncontrado as exc:
            raise Http404 from exc
        except FeedbackJaAnalisado as exc:
            messages.error(request, str(exc))
            return redirect("feedbacks:fila")
        except MotivoDeRejeicaoInvalido as exc:
            form.add_error("texto", str(exc))
            return _exibir_analise(request, feedback, AceitarFeedbackForm(feedback=feedback), form)
        messages.success(request, "Feedback rejeitado.")
        return redirect("feedbacks:fila")


def _feedback_ou_404(feedback_id: int):
    try:
        return AnaliseService.obter_para_analise(feedback_id)
    except FeedbackNaoEncontrado as exc:
        raise Http404 from exc


def _exibir_analise(request, feedback, form_aceitar, form_rejeitar):
    contexto = {
        "feedback": feedback,
        "trecho": feedback.trecho,
        "outros": AnaliseService.outros_do_trecho(feedback)[:10],
        "form_aceitar": form_aceitar,
        "form_rejeitar": form_rejeitar,
    }
    return render(request, TEMPLATE_ANALISAR, contexto)
