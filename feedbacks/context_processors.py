from feedbacks.services import NotificacaoService


def notificacoes(request) -> dict:
    """Expõe ao base.html quantas notificações o usuário ainda não leu."""
    if not request.user.is_authenticated:
        return {}
    return {"notificacoes_nao_lidas": NotificacaoService.contar_nao_lidas(request.user)}
