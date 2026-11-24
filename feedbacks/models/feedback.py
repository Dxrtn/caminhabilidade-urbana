from django.conf import settings
from django.db import models
from django.db.models import Q

from comum.models import ModeloComDatas
from feedbacks.models.escolhas import (
    CLASSIFICACOES_SUGERIVEIS,
    MotivoRejeicao,
    StatusFeedback,
    TipoFeedback,
)
from trechos.models import Classificacao

DESCRICAO_MINIMO = 10
DESCRICAO_MAXIMO = 500

_REJEITADO = Q(status=StatusFeedback.REJEITADO)
_EM_ANALISE = Q(status=StatusFeedback.EM_ANALISE)


class Feedback(ModeloComDatas):
    # Nulo só se a conta for removida: o relato continua, anônimo.
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DB_SET_NULL,
        null=True,
        related_name="feedbacks",
    )
    # DO_NOTHING no lugar de PROTECT (ADR 0008): o NO ACTION do banco impede excluir o trecho.
    trecho = models.ForeignKey("trechos.Trecho", on_delete=models.DO_NOTHING, related_name="feedbacks")
    tipo = models.CharField(max_length=25, choices=TipoFeedback.choices)
    classificacao_sugerida = models.CharField(
        "classificação sugerida",
        max_length=15,
        choices=Classificacao.choices,
        null=True,
        blank=True,
    )
    descricao = models.TextField("descrição")
    obstaculos = models.ManyToManyField(
        "trechos.Obstaculo", through="feedbacks.FeedbackObstaculo", blank=True
    )
    enviado_a_distancia = models.BooleanField(default=False)
    status = models.CharField(max_length=12, choices=StatusFeedback.choices, default=StatusFeedback.EM_ANALISE)
    motivo_rejeicao = models.CharField(
        "motivo da rejeição",
        max_length=25,
        choices=MotivoRejeicao.choices,
        null=True,
        blank=True,
    )
    motivo_rejeicao_texto = models.CharField(max_length=300, blank=True, default="")
    analisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DB_SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    analisado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "feedback"
        constraints = [
            models.CheckConstraint(condition=Q(tipo__in=TipoFeedback.values), name="ck_feedback_tipo_valido"),
            models.CheckConstraint(
                condition=Q(status__in=StatusFeedback.values), name="ck_feedback_status_valido"
            ),
            models.CheckConstraint(
                condition=Q(classificacao_sugerida__isnull=True)
                | Q(classificacao_sugerida__in=CLASSIFICACOES_SUGERIVEIS),
                name="ck_feedback_classificacao_sugerida_valida",
            ),
            # Não está na tabela da spec, mas a skill postgresql exige CHECK em todo campo com choices.
            models.CheckConstraint(
                condition=Q(motivo_rejeicao__isnull=True) | Q(motivo_rejeicao__in=MotivoRejeicao.values),
                name="ck_feedback_motivo_rejeicao_valido",
            ),
            models.CheckConstraint(
                condition=Q(descricao__length__gte=DESCRICAO_MINIMO, descricao__length__lte=DESCRICAO_MAXIMO),
                name="ck_feedback_descricao_tamanho",
            ),
            # REJEITADO se e somente se houver motivo.
            models.CheckConstraint(
                condition=(_REJEITADO & Q(motivo_rejeicao__isnull=False))
                | (~_REJEITADO & Q(motivo_rejeicao__isnull=True)),
                name="ck_feedback_rejeicao_exige_motivo",
            ),
            models.CheckConstraint(
                condition=~Q(motivo_rejeicao=MotivoRejeicao.OUTRO) | ~Q(motivo_rejeicao_texto=""),
                name="ck_feedback_motivo_outro_exige_texto",
            ),
            # EM_ANALISE se e somente se ainda não houver data de análise.
            models.CheckConstraint(
                condition=(_EM_ANALISE & Q(analisado_em__isnull=True))
                | (~_EM_ANALISE & Q(analisado_em__isnull=False)),
                name="ck_feedback_analise_exige_data",
            ),
            # Índice único parcial: 1 feedback em análise por usuário e trecho (RF-21).
            models.UniqueConstraint(
                fields=["usuario", "trecho"],
                condition=_EM_ANALISE,
                name="uq_feedback_um_em_analise_por_trecho",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "criado_em"], name="idx_feedback_status_criado"),
        ]

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} em {self.trecho_id} ({self.get_status_display()})"


class FeedbackObstaculo(models.Model):
    feedback = models.ForeignKey("feedbacks.Feedback", on_delete=models.DB_CASCADE)
    obstaculo = models.ForeignKey("trechos.Obstaculo", on_delete=models.DO_NOTHING)

    class Meta:
        db_table = "feedback_obstaculo"
        verbose_name = "obstáculo do feedback"
        verbose_name_plural = "obstáculos dos feedbacks"
        constraints = [
            models.UniqueConstraint(fields=["feedback", "obstaculo"], name="uq_feedback_obstaculo"),
        ]

    def __str__(self) -> str:
        return f"{self.obstaculo_id} em {self.feedback_id}"


class FotoFeedback(models.Model):
    """Foto enviada pelo usuário; só fica pública depois de aprovada (spec 0007)."""

    feedback = models.ForeignKey("feedbacks.Feedback", on_delete=models.DB_CASCADE, related_name="fotos")
    imagem = models.ImageField(upload_to="feedbacks/%Y/%m/")
    aprovada = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "foto_feedback"
        verbose_name = "foto do feedback"
        verbose_name_plural = "fotos dos feedbacks"

    def __str__(self) -> str:
        return f"Foto {self.pk} do feedback {self.feedback_id}"


class Notificacao(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.DB_CASCADE, related_name="notificacoes"
    )
    feedback = models.ForeignKey(
        "feedbacks.Feedback", on_delete=models.DB_CASCADE, related_name="notificacoes"
    )
    mensagem = models.CharField(max_length=200)
    lida = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notificacao"
        verbose_name = "notificação"
        verbose_name_plural = "notificações"

    def __str__(self) -> str:
        return self.mensagem
