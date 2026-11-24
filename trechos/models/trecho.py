from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Now

from comum.models import ModeloComDatas
from trechos.models.escolhas import (
    LATITUDE_MAXIMA,
    LATITUDE_MINIMA,
    LONGITUDE_MAXIMA,
    LONGITUDE_MINIMA,
    Classificacao,
    Lado,
)

OBSERVACOES_MAXIMO = 500


def _coordenadas_em_maceio() -> Q:
    latitudes = Q(
        lat_inicio__range=(LATITUDE_MINIMA, LATITUDE_MAXIMA),
        lat_fim__range=(LATITUDE_MINIMA, LATITUDE_MAXIMA),
    )
    longitudes = Q(
        lng_inicio__range=(LONGITUDE_MINIMA, LONGITUDE_MAXIMA),
        lng_fim__range=(LONGITUDE_MINIMA, LONGITUDE_MAXIMA),
    )
    return latitudes & longitudes


class Trecho(ModeloComDatas):
    """Trecho de calçada entre dois pontos.

    on_delete: DO_NOTHING faz o papel de PROTECT (ADR 0008). O Django 6.1 não deixa
    misturar PROTECT com DB_CASCADE/DB_SET_NULL; com DO_NOTHING, o banco fica com
    NO ACTION, que impede excluir um bairro, obstáculo ou trecho em uso.
    """

    logradouro = models.CharField(max_length=150)
    bairro =models.ForeignKey("trechos.Bairro", on_delete=models.DO_NOTHING, related_name="trechos")
    referencia_inicio = models.CharField("referência de início", max_length=150)
    referencia_fim = models.CharField("referência de fim", max_length=150)
    lado = models.CharField(max_length=5, choices=Lado.choices)
    lat_inicio = models.DecimalField("latitude de início", max_digits=9, decimal_places=6)
    lng_inicio = models.DecimalField("longitude de início", max_digits=9, decimal_places=6)
    lat_fim = models.DecimalField("latitude de fim", max_digits=9, decimal_places=6)
    lng_fim = models.DecimalField("longitude de fim", max_digits=9, decimal_places=6)
    classificacao = models.CharField(
        "classificação",
        max_length=15,
        choices=Classificacao.choices,
        default=Classificacao.SEM_AVALIACAO,
    )
    obstaculos = models.ManyToManyField(
        "trechos.Obstaculo", through="trechos.TrechoObstaculo", blank=True
    )
    ativo = models.BooleanField(default=True)
    observacoes = models.TextField("observações", blank=True, default="")
    # A trigger trg_trecho_historico copia este campo para historico_trecho.alterado_por_id.
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DB_SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        db_table = "trecho"
        constraints = [
            models.CheckConstraint(
                condition=Q(classificacao__in=Classificacao.values),
                name="ck_trecho_classificacao_valida",
            ),
            models.CheckConstraint(condition=Q(lado__in=Lado.values), name="ck_trecho_lado_valido"),
            models.CheckConstraint(condition=_coordenadas_em_maceio(), name="ck_trecho_coordenadas_em_maceio"),
            models.CheckConstraint(
                condition=~Q(lat_inicio=F("lat_fim"), lng_inicio=F("lng_fim")),
                name="ck_trecho_pontos_distintos",
            ),
            models.CheckConstraint(
                condition=Q(observacoes__length__lte=OBSERVACOES_MAXIMO),
                name="ck_trecho_observacoes_tamanho",
            ),
            models.UniqueConstraint(
                fields=["logradouro", "referencia_inicio", "referencia_fim", "lado"],
                name="uq_trecho_logradouro_referencias_lado",
            ),
        ]
        indexes = [
            # O Django limita nomes de índice a 30 caracteres; por isso "classif".
            models.Index(fields=["bairro", "classificacao"], name="idx_trecho_bairro_classif"),
        ]

    def __str__(self) -> str:
        return f"{self.logradouro} ({self.referencia_inicio} → {self.referencia_fim})"


class TrechoObstaculo(models.Model):
    trecho = models.ForeignKey("trechos.Trecho", on_delete=models.DB_CASCADE)
    obstaculo = models.ForeignKey("trechos.Obstaculo", on_delete=models.DO_NOTHING)

    class Meta:
        db_table = "trecho_obstaculo"
        verbose_name = "obstáculo do trecho"
        verbose_name_plural = "obstáculos dos trechos"
        constraints = [
            models.UniqueConstraint(fields=["trecho", "obstaculo"], name="uq_trecho_obstaculo"),
        ]

    def __str__(self) -> str:
        return f"{self.obstaculo_id} em {self.trecho_id}"


class FotoTrecho(models.Model):
    """Foto cadastrada pela equipe; sempre pública."""

    trecho = models.ForeignKey("trechos.Trecho", on_delete=models.DB_CASCADE, related_name="fotos")
    imagem = models.ImageField(upload_to="trechos/%Y/%m/")
    descricao = models.CharField("descrição", max_length=150, blank=True, help_text="Texto alternativo da foto.")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "foto_trecho"
        verbose_name = "foto do trecho"
        verbose_name_plural = "fotos dos trechos"

    def __str__(self) -> str:
        return self.descricao or f"Foto {self.pk}"


class HistoricoTrecho(models.Model):
    """Preenchido SOMENTE pela trigger trg_trecho_historico.

    Os nomes das colunas (trecho_id, classificacao_anterior, classificacao_nova,
    alterado_por_id, alterado_em) são os do INSERT da trigger.
    """

    trecho = models.ForeignKey("trechos.Trecho", on_delete=models.DB_CASCADE, related_name="historico")
    classificacao_anterior = models.CharField(max_length=15, null=True)
    classificacao_nova = models.CharField(max_length=15)
    alterado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DB_SET_NULL,
        null=True,
        related_name="+",
    )
    alterado_em = models.DateTimeField(db_default=Now())

    class Meta:
        db_table = "historico_trecho"
        verbose_name = "histórico do trecho"
        verbose_name_plural = "históricos dos trechos"
        ordering = ["alterado_em", "id"]

    def __str__(self) -> str:
        return f"{self.trecho_id}: {self.classificacao_anterior} → {self.classificacao_nova}"
