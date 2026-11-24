"""Tabelas de referência, preenchidas pela migração 0002_dados_de_referencia."""

from django.db import models


class Bairro(models.Model):
    nome = models.CharField(max_length=80, unique=True)

    class Meta:
        db_table = "bairro"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class Obstaculo(models.Model):
    codigo = models.SlugField(max_length=40, unique=True)
    nome = models.CharField(max_length=60, unique=True)

    class Meta:
        db_table = "obstaculo"
        verbose_name = "obstáculo"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome
