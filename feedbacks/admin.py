from django.contrib import admin

from comum.admin import SomenteLeituraAdmin
from feedbacks.models import Feedback, FeedbackObstaculo, FotoFeedback, Notificacao


@admin.register(Feedback)
class FeedbackAdmin(SomenteLeituraAdmin):
    list_display = ("trecho", "tipo", "status", "usuario", "criado_em")
    list_filter = ("status", "tipo")
    list_select_related = ("trecho", "usuario")


@admin.register(FeedbackObstaculo)
class FeedbackObstaculoAdmin(SomenteLeituraAdmin):
    list_display = ("feedback", "obstaculo")
    list_select_related = ("feedback", "obstaculo")


@admin.register(FotoFeedback)
class FotoFeedbackAdmin(SomenteLeituraAdmin):
    list_display = ("feedback", "aprovada", "criado_em")
    list_filter = ("aprovada",)
    list_select_related = ("feedback",)


@admin.register(Notificacao)
class NotificacaoAdmin(SomenteLeituraAdmin):
    list_display = ("usuario", "mensagem", "lida", "criado_em")
    list_filter = ("lida",)
    list_select_related = ("usuario",)
