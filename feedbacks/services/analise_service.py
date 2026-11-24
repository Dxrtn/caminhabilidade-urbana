from collections.abc import Iterable

from django.core.paginator import Page, Paginator
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from feedbacks.exceptions import FeedbackJaAnalisado, FeedbackNaoEncontrado, MotivoDeRejeicaoInvalido
from feedbacks.models import Feedback, FotoFeedback, MotivoRejeicao, StatusFeedback, TipoFeedback
from feedbacks.services.notificacao_service import NotificacaoService
from trechos.services import TrechoService

POR_PAGINA = 10


class AnaliseService:
    @classmethod
    def fila(cls, pagina: int | str | None = 1, bairro_id: int | None = None, tipo: str | None = None) -> Page:
        # Do mais antigo para o mais recente: usa o índice idx_feedback_status_criado.
        feedbacks = (
            Feedback.objects.filter(status=StatusFeedback.EM_ANALISE)
            .select_related("trecho__bairro", "usuario")
            .prefetch_related("obstaculos", "fotos")
            .order_by("criado_em", "id")
        )
        if bairro_id:
            feedbacks = feedbacks.filter(trecho__bairro_id=bairro_id)
        if tipo in TipoFeedback.values:
            feedbacks = feedbacks.filter(tipo=tipo)
        return Paginator(feedbacks, POR_PAGINA).get_page(pagina)

    @classmethod
    def contar_em_analise(cls) -> int:
        return Feedback.objects.filter(status=StatusFeedback.EM_ANALISE).count()

    @classmethod
    def obter_para_analise(cls, feedback_id: int) -> Feedback:
        feedback = (
            Feedback.objects.select_related("trecho__bairro", "usuario", "analisado_por")
            .prefetch_related("obstaculos", "fotos", "trecho__obstaculos")
            .filter(pk=feedback_id)
            .first()
        )
        if feedback is None:
            raise FeedbackNaoEncontrado()
        return feedback

    @classmethod
    def outros_do_trecho(cls, feedback: Feedback) -> QuerySet[Feedback]:
        return (
            Feedback.objects.filter(trecho_id=feedback.trecho_id)
            .exclude(pk=feedback.pk)
            .order_by("-criado_em", "-id")
        )

    @classmethod
    def aceitar(
        cls,
        feedback_id: int,
        administrador,
        nova_classificacao: str | None = None,
        obstaculo_codigos: Iterable[str] | None = None,
        fotos_aprovadas_ids: Iterable[int] = (),
    ) -> Feedback:
        with transaction.atomic():
            feedback = cls._obter_em_analise(feedback_id)
            cls._registrar_analise(feedback, administrador, StatusFeedback.ACEITO)

            if nova_classificacao or obstaculo_codigos is not None:
                # Sem nova classificação, mantém a atual: a trigger só grava histórico se ela mudar.
                TrechoService.alterar_classificacao(
                    feedback.trecho_id,
                    nova_classificacao or feedback.trecho.classificacao,
                    administrador,
                    obstaculo_codigos=obstaculo_codigos,
                )
            # Só fotos deste feedback, mesmo que venham ids de outro.
            FotoFeedback.objects.filter(feedback=feedback, pk__in=list(fotos_aprovadas_ids)).update(aprovada=True)
            NotificacaoService.notificar(
                feedback, f"Seu feedback sobre {feedback.trecho.logradouro} foi aceito. Obrigado!"
            )
        return feedback

    @classmethod
    def rejeitar(cls, feedback_id: int, administrador, motivo: str, texto: str = "") -> Feedback:
        texto = (texto or "").strip()
        with transaction.atomic():
            feedback = cls._obter_em_analise(feedback_id)
            if motivo not in MotivoRejeicao.values or (motivo == MotivoRejeicao.OUTRO and not texto):
                raise MotivoDeRejeicaoInvalido()
            feedback.motivo_rejeicao = motivo
            feedback.motivo_rejeicao_texto = texto
            cls._registrar_analise(feedback, administrador, StatusFeedback.REJEITADO)

            rotulo = MotivoRejeicao(motivo).label
            detalhe = f" ({texto})" if texto else ""
            NotificacaoService.notificar(
                feedback, f"Seu feedback sobre {feedback.trecho.logradouro} não foi aceito. Motivo: {rotulo}{detalhe}."
            )
        return feedback

    # ---------- auxiliares

    @staticmethod
    def _obter_em_analise(feedback_id: int) -> Feedback:
        """Trava a linha: dois administradores não analisam o mesmo feedback ao mesmo tempo."""
        feedback = (
            Feedback.objects.select_for_update(of=("self",))  # trava só o feedback, não o trecho
            .select_related("trecho")
            .filter(pk=feedback_id)
            .first()
        )
        if feedback is None:
            raise FeedbackNaoEncontrado()
        if feedback.status != StatusFeedback.EM_ANALISE:
            raise FeedbackJaAnalisado()
        return feedback

    @staticmethod
    def _registrar_analise(feedback: Feedback, administrador, status: str) -> None:
        feedback.status = status
        feedback.analisado_por = administrador
        feedback.analisado_em = timezone.now()
        feedback.save(
            update_fields=[
                "status",
                "analisado_por",
                "analisado_em",
                "motivo_rejeicao",
                "motivo_rejeicao_texto",
                "atualizado_em",
            ]
        )
