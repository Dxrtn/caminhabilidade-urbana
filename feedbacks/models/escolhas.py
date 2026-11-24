from django.db import models

from trechos.models import Classificacao


class TipoFeedback(models.TextChoices):
    NOVO_PROBLEMA = "NOVO_PROBLEMA", "Novo problema"
    PROBLEMA_RESOLVIDO = "PROBLEMA_RESOLVIDO", "Problema resolvido"
    CLASSIFICACAO_INCORRETA = "CLASSIFICACAO_INCORRETA", "Classificação incorreta"


class StatusFeedback(models.TextChoices):
    EM_ANALISE = "EM_ANALISE", "Em análise"
    ACEITO = "ACEITO", "Aceito"
    REJEITADO = "REJEITADO", "Rejeitado"


class MotivoRejeicao(models.TextChoices):
    FOTO_NAO_CORRESPONDE = "FOTO_NAO_CORRESPONDE", "Foto não corresponde ao local"
    INFORMACAO_INCORRETA = "INFORMACAO_INCORRETA", "Informação incorreta"
    CONTEUDO_IMPROPRIO = "CONTEUDO_IMPROPRIO", "Conteúdo impróprio"
    DUPLICADO = "DUPLICADO", "Duplicado"
    OUTRO = "OUTRO", "Outro"


# O usuário sugere uma avaliação; "Sem avaliação" não é uma sugestão possível.
CLASSIFICACOES_SUGERIVEIS = [
    Classificacao.ACESSIVEL,
    Classificacao.PARCIAL,
    Classificacao.INACESSIVEL,
]
