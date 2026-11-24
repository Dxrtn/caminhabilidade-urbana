from django.db import models


class ModeloComDatas(models.Model):
    """Datas de criação e de última alteração, herdadas pelos models que precisam delas."""

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
