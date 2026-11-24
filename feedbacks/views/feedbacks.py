from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect, render
from django.views import View

from feedbacks.exceptions import FeedbackErro, FeedbackNaoEncontrado, FeedbackNaoPodeSerExcluido
from feedbacks.forms import FeedbackForm
from feedbacks.services import FeedbackService, NotificacaoService
from trechos.exceptions import TrechoNaoEncontrado


class FeedbackCreateView(LoginRequiredMixin, View):
    template_name = "feedbacks/enviar.html"

    def get(self, request, trecho_id):
        trecho = _trecho_ou_404(trecho_id)
        return render(request, self.template_name, {"form": FeedbackForm(), "trecho": trecho})

    def post(self, request, trecho_id):
        trecho = _trecho_ou_404(trecho_id)
        form = FeedbackForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "trecho": trecho})

        dados = form.cleaned_data
        try:
            FeedbackService.enviar(
                request.user,
                trecho_id,
                tipo=dados["tipo"],
                descricao=dados["descricao"],
                obstaculo_ids=[obstaculo.pk for obstaculo in dados["obstaculos"]],
                classificacao_sugerida=dados["classificacao_sugerida"] or None,
                fotos=dados["fotos"],
                latitude=dados["latitude"],
                longitude=dados["longitude"],
            )
        except TrechoNaoEncontrado as exc:
            raise Http404 from exc
        except FeedbackErro as exc:
            # Polimorfismo: qualquer erro de feedback chega aqui, cada um com sua mensagem.
            form.add_error(None, str(exc))
            return render(request, self.template_name, {"form": form, "trecho": trecho})

        messages.success(request, "Feedback enviado! Ele será analisado pela nossa equipe.")
        return redirect("trechos:detalhe", trecho_id=trecho_id)


class MeusFeedbacksView(LoginRequiredMixin, View):
    def get(self, request):
        pagina = FeedbackService.listar_do_usuario(request.user, request.GET.get("pagina"))
        notificacoes = list(NotificacaoService.listar_recentes(request.user))
        # Marca antes de renderizar: o contador do menu já aparece zerado nesta página.
        NotificacaoService.marcar_todas_como_lidas(request.user)
        return render(request, "feedbacks/meus_feedbacks.html", {"pagina": pagina, "notificacoes": notificacoes})


class FeedbackExcluirView(LoginRequiredMixin, View):
    def post(self, request, feedback_id):
        try:
            FeedbackService.excluir(feedback_id, request.user)
        except FeedbackNaoEncontrado as exc:
            raise Http404 from exc
        except FeedbackNaoPodeSerExcluido as exc:
            messages.error(request, str(exc))
            return redirect("feedbacks:meus")
        messages.success(request, "Feedback excluído.")
        return redirect("feedbacks:meus")


def _trecho_ou_404(trecho_id: int):
    try:
        return FeedbackService.obter_trecho(trecho_id)
    except TrechoNaoEncontrado as exc:
        raise Http404 from exc
