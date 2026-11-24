from django.urls import path

from feedbacks.views import (
    AceitarFeedbackView,
    AnalisarFeedbackView,
    FeedbackCreateView,
    FeedbackExcluirView,
    FilaAnaliseView,
    MeusFeedbacksView,
    RejeitarFeedbackView,
)

app_name = "feedbacks"

urlpatterns = [
    path("trechos/<int:trecho_id>/feedback/", FeedbackCreateView.as_view(), name="enviar"),
    path("meus-feedbacks/", MeusFeedbacksView.as_view(), name="meus"),
    path("meus-feedbacks/<int:feedback_id>/excluir/", FeedbackExcluirView.as_view(), name="excluir"),
    path("painel/feedbacks/", FilaAnaliseView.as_view(), name="fila"),
    path("painel/feedbacks/<int:feedback_id>/", AnalisarFeedbackView.as_view(), name="analisar"),
    path("painel/feedbacks/<int:feedback_id>/aceitar/", AceitarFeedbackView.as_view(), name="aceitar"),
    path("painel/feedbacks/<int:feedback_id>/rejeitar/", RejeitarFeedbackView.as_view(), name="rejeitar"),
]
