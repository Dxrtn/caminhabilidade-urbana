from django.contrib import admin

from comum.admin import SomenteLeituraAdmin
from trechos.models import (
    Bairro,
    FotoTrecho,
    HistoricoTrecho,
    Obstaculo,
    Trecho,
    TrechoMapa,
    TrechoObstaculo,
)


# Bairro e Obstaculo podem ser editados. A exclusão fica bloqueada: com DO_NOTHING
# (ADR 0008), excluir um registro em uso só falharia no banco, com erro 500.
@admin.register(Bairro)
class BairroAdmin(admin.ModelAdmin):
    search_fields = ("nome",)

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Obstaculo)
class ObstaculoAdmin(admin.ModelAdmin):
    list_display = ("nome", "codigo")
    search_fields = ("nome", "codigo")

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Trecho)
class TrechoAdmin(SomenteLeituraAdmin):
    list_display = ("logradouro", "bairro", "lado", "classificacao", "ativo", "atualizado_em")
    list_filter = ("classificacao", "ativo", "bairro")
    search_fields = ("logradouro", "referencia_inicio", "referencia_fim")
    list_select_related = ("bairro",)


@admin.register(TrechoObstaculo)
class TrechoObstaculoAdmin(SomenteLeituraAdmin):
    list_display = ("trecho", "obstaculo")
    list_select_related = ("trecho", "obstaculo")


@admin.register(FotoTrecho)
class FotoTrechoAdmin(SomenteLeituraAdmin):
    list_display = ("trecho", "descricao", "criado_em")
    list_select_related = ("trecho",)


@admin.register(HistoricoTrecho)
class HistoricoTrechoAdmin(SomenteLeituraAdmin):
    list_display = ("trecho", "classificacao_anterior", "classificacao_nova", "alterado_por", "alterado_em")
    list_select_related = ("trecho", "alterado_por")


@admin.register(TrechoMapa)
class TrechoMapaAdmin(SomenteLeituraAdmin):
    list_display = ("logradouro", "bairro", "classificacao", "dias_sem_atualizacao", "feedbacks_em_analise")
    list_filter = ("classificacao",)
