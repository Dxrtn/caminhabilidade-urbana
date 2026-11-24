from django.db import NotSupportedError, models

from trechos.models.escolhas import Classificacao, Lado


class TrechoMapa(models.Model):
    """Leitura da view vw_trechos_mapa (criada na migração feedbacks/0002).

    managed = False: o Django não cria nem altera nada no banco para este model.
    """

    id = models.BigIntegerField(primary_key=True)
    logradouro = models.CharField(max_length=150)
    bairro_id = models.BigIntegerField()
    bairro = models.CharField(max_length=80)
    referencia_inicio = models.CharField(max_length=150)
    referencia_fim = models.CharField(max_length=150)
    lado = models.CharField(max_length=5, choices=Lado.choices)
    lat_inicio = models.DecimalField(max_digits=9, decimal_places=6)
    lng_inicio = models.DecimalField(max_digits=9, decimal_places=6)
    lat_fim = models.DecimalField(max_digits=9, decimal_places=6)
    lng_fim = models.DecimalField(max_digits=9, decimal_places=6)
    classificacao = models.CharField(max_length=15, choices=Classificacao.choices)
    atualizado_em = models.DateTimeField()
    dias_sem_atualizacao = models.IntegerField()
    feedbacks_em_analise = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = "vw_trechos_mapa"
        verbose_name = "trecho no mapa"
        verbose_name_plural = "trechos no mapa"

    def __str__(self) -> str:
        return self.logradouro

    def save(self, *args, **kwargs):
        raise NotSupportedError("vw_trechos_mapa é somente leitura.")

    def delete(self, *args, **kwargs):
        raise NotSupportedError("vw_trechos_mapa é somente leitura.")
