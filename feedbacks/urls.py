from django.urls import path

from feedbacks.views import FeedbackCreateView, FeedbackExcluirView, MeusFeedbacksView

app_name = "feedbacks"

urlpatterns = [
    path("trechos/<int:trecho_id>/feedback/", FeedbackCreateView.as_view(), name="enviar"),
    path("meus-feedbacks/", MeusFeedbacksView.as_view(), name="meus"),
    path("meus-feedbacks/<int:feedback_id>/excluir/", FeedbackExcluirView.as_view(), name="excluir"),
]
