from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

FORMATO_CODIGO = r"^[0-9]{6}$"


class CodigoVerificacao(models.Model):
    """Código de 6 dígitos enviado por SMS para confirmar o celular (spec 0002)."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DB_CASCADE,
        related_name="codigos",
    )
    codigo = models.CharField(max_length=6)
    criado_em = models.DateTimeField(default=timezone.now)
    expira_em = models.DateTimeField()
    usado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "codigo_verificacao"
        verbose_name = "código de verificação"
        verbose_name_plural = "códigos de verificação"
        constraints = [
            models.CheckConstraint(
                condition=Q(codigo__regex=FORMATO_CODIGO),
                name="ck_codigo_seis_digitos",
            ),
            models.CheckConstraint(
                condition=Q(expira_em__gt=F("criado_em")),
                name="ck_codigo_expira_depois_de_criado",
            ),
        ]

    def __str__(self) -> str:
        return f"Código do usuário {self.usuario_id} criado em {self.criado_em:%d/%m/%Y %H:%M}"
