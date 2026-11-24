from django.db.models import QuerySet

from feedbacks.models import Feedback, Notificacao

TAMANHO_MAXIMO_DA_MENSAGEM = 200


class NotificacaoService:
    @classmethod
    def notificar(cls, feedback: Feedback, mensagem: str) -> Notificacao | None:
        """Avisa o autor do feedback. Sem autor (conta removida), não há a quem avisar."""
        if feedback.usuario_id is None:
            return None
        return Notificacao.objects.create(
            usuario_id=feedback.usuario_id,
            feedback=feedback,
            mensagem=mensagem[:TAMANHO_MAXIMO_DA_MENSAGEM],
        )

    @classmethod
    def contar_nao_lidas(cls, usuario) -> int:
        return Notificacao.objects.filter(usuario=usuario, lida=False).count()

    @classmethod
    def listar_recentes(cls, usuario, limite: int = 10) -> QuerySet[Notificacao]:
        return Notificacao.objects.filter(usuario=usuario).order_by("-criado_em", "-id")[:limite]

    @classmethod
    def marcar_todas_como_lidas(cls, usuario) -> int:
        return Notificacao.objects.filter(usuario=usuario, lida=False).update(lida=True)
