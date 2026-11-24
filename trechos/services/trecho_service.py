from collections.abc import Iterable
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile
from django.core.paginator import Page, Paginator
from django.db import IntegrityError, transaction
from django.db.models import QuerySet
from django.utils import timezone

from trechos.exceptions import DadosDeTrechoInvalidos, TrechoDuplicado, TrechoErro, TrechoNaoEncontrado
from trechos.models import (
    Bairro,
    Classificacao,
    FotoTrecho,
    HistoricoTrecho,
    Lado,
    Obstaculo,
    Trecho,
    TrechoObstaculo,
)
from trechos.services.dados import DadosTrecho

POR_PAGINA = 10
DIAS_PARA_DESATUALIZADO = 180


class TrechoService:
    @classmethod
    def listar_para_gestao(
        cls,
        texto: str | None = None,
        bairro_id: int | None = None,
        classificacao: str | None = None,
        desatualizados: bool = False,
        pagina: int | str | None = 1,
    ) -> Page:
        trechos = Trecho.objects.select_related("bairro").order_by("logradouro", "id")
        if texto:
            trechos = trechos.filter(logradouro__icontains=texto)
        if bairro_id:
            trechos = trechos.filter(bairro_id=bairro_id)
        if classificacao:
            trechos = trechos.filter(classificacao=classificacao)
        if desatualizados:
            limite = timezone.now() - timedelta(days=DIAS_PARA_DESATUALIZADO)
            trechos = trechos.filter(atualizado_em__lt=limite)
        return Paginator(trechos, POR_PAGINA).get_page(pagina)

    @classmethod
    def obter(cls, trecho_id: int) -> Trecho:
        trecho = Trecho.objects.select_related("bairro").filter(pk=trecho_id).first()
        if trecho is None:
            raise TrechoNaoEncontrado()
        return trecho

    @classmethod
    def criar(cls, dados: DadosTrecho, administrador, fotos: Iterable[UploadedFile] = ()) -> Trecho:
        bairro, obstaculos = cls._validar(dados)
        if cls._existe_igual(dados):
            raise TrechoDuplicado()
        try:
            with transaction.atomic():
                trecho = Trecho.objects.create(
                    **cls._campos(dados), bairro=bairro, atualizado_por=administrador
                )
                cls._definir_obstaculos(trecho, obstaculos)
                cls._gravar_fotos(trecho, fotos)
        except IntegrityError:
            # Garantia: outro cadastro gravou o mesmo trecho entre a verificação e o INSERT.
            if cls._existe_igual(dados):
                raise TrechoDuplicado() from None
            raise
        return trecho

    @classmethod
    def atualizar(
        cls, trecho_id: int, dados: DadosTrecho, administrador, novas_fotos: Iterable[UploadedFile] = ()
    ) -> Trecho:
        bairro, obstaculos = cls._validar(dados)
        with transaction.atomic():
            trecho = cls._obter_para_alterar(trecho_id)
            if cls._existe_igual(dados, exceto_id=trecho.pk):
                raise TrechoDuplicado()
            for campo, valor in cls._campos(dados).items():
                setattr(trecho, campo, valor)
            trecho.bairro = bairro
            trecho.atualizado_por = administrador
            trecho.save()  # a trigger grava o histórico se a classificação mudou
            cls._definir_obstaculos(trecho, obstaculos)
            cls._gravar_fotos(trecho, novas_fotos)
        return trecho

    @classmethod
    def alterar_classificacao(
        cls,
        trecho_id: int,
        classificacao: str,
        administrador,
        obstaculo_codigos: Iterable[str] | None = None,
    ) -> Trecho:
        if classificacao not in Classificacao.values:
            raise DadosDeTrechoInvalidos(f"Classificação '{classificacao}' não existe.")
        obstaculos = None if obstaculo_codigos is None else cls._resolver_obstaculos(obstaculo_codigos)
        with transaction.atomic():
            trecho = cls._obter_para_alterar(trecho_id)
            trecho.classificacao = classificacao
            trecho.atualizado_por = administrador
            trecho.save(update_fields=["classificacao", "atualizado_por", "atualizado_em"])
            if obstaculos is not None:
                cls._definir_obstaculos(trecho, obstaculos)
        return trecho

    @classmethod
    def desativar(cls, trecho_id: int, administrador) -> Trecho:
        return cls._definir_ativo(trecho_id, administrador, ativo=False)

    @classmethod
    def reativar(cls, trecho_id: int, administrador) -> Trecho:
        return cls._definir_ativo(trecho_id, administrador, ativo=True)

    @classmethod
    def historico(cls, trecho_id: int) -> QuerySet[HistoricoTrecho]:
        trecho = cls.obter(trecho_id)
        return trecho.historico.select_related("alterado_por").order_by("-alterado_em", "-id")

    @classmethod
    def obter_administrador(cls, email: str):
        """Usuário is_staff com o e-mail informado, usado pela carga em lote."""
        administrador = (
            get_user_model().objects.filter(email__iexact=email, is_staff=True, is_active=True).first()
        )
        if administrador is None:
            raise TrechoErro(f"'{email}' não é um administrador ativo.")
        return administrador

    # ---------- auxiliares

    @staticmethod
    def _campos(dados: DadosTrecho) -> dict:
        return {
            "logradouro": dados.logradouro,
            "referencia_inicio": dados.referencia_inicio,
            "referencia_fim": dados.referencia_fim,
            "lado": dados.lado,
            "lat_inicio": dados.lat_inicio,
            "lng_inicio": dados.lng_inicio,
            "lat_fim": dados.lat_fim,
            "lng_fim": dados.lng_fim,
            "classificacao": dados.classificacao,
            "observacoes": dados.observacoes,
        }

    @classmethod
    def _validar(cls, dados: DadosTrecho) -> tuple[Bairro, list[Obstaculo]]:
        if dados.lado not in Lado.values:
            raise DadosDeTrechoInvalidos(f"Lado '{dados.lado}' não existe.")
        if dados.classificacao not in Classificacao.values:
            raise DadosDeTrechoInvalidos(f"Classificação '{dados.classificacao}' não existe.")
        bairro = Bairro.objects.filter(nome__iexact=dados.bairro.strip()).first()
        if bairro is None:
            raise DadosDeTrechoInvalidos(f"Bairro '{dados.bairro}' não existe.")
        return bairro, cls._resolver_obstaculos(dados.obstaculos)

    @staticmethod
    def _resolver_obstaculos(codigos: Iterable[str]) -> list[Obstaculo]:
        codigos = set(codigos)
        obstaculos = list(Obstaculo.objects.filter(codigo__in=codigos))
        faltando = codigos - {o.codigo for o in obstaculos}
        if faltando:
            raise DadosDeTrechoInvalidos(f"Obstáculo '{sorted(faltando)[0]}' não existe.")
        return obstaculos

    @staticmethod
    def _existe_igual(dados: DadosTrecho, exceto_id: int | None = None) -> bool:
        iguais = Trecho.objects.filter(
            logradouro=dados.logradouro,
            referencia_inicio=dados.referencia_inicio,
            referencia_fim=dados.referencia_fim,
            lado=dados.lado,
        )
        if exceto_id is not None:
            iguais = iguais.exclude(pk=exceto_id)
        return iguais.exists()

    @staticmethod
    def _obter_para_alterar(trecho_id: int) -> Trecho:
        trecho = Trecho.objects.select_for_update().filter(pk=trecho_id).first()
        if trecho is None:
            raise TrechoNaoEncontrado()
        return trecho

    @staticmethod
    def _definir_obstaculos(trecho: Trecho, obstaculos: list[Obstaculo]) -> None:
        TrechoObstaculo.objects.filter(trecho=trecho).delete()
        TrechoObstaculo.objects.bulk_create(
            [TrechoObstaculo(trecho=trecho, obstaculo=obstaculo) for obstaculo in obstaculos]
        )

    @staticmethod
    def _gravar_fotos(trecho: Trecho, fotos: Iterable[UploadedFile]) -> None:
        for foto in fotos:
            FotoTrecho.objects.create(trecho=trecho, imagem=foto, descricao=f"Foto de {trecho.logradouro}"[:150])

    @classmethod
    def _definir_ativo(cls, trecho_id: int, administrador, *, ativo: bool) -> Trecho:
        with transaction.atomic():
            trecho = cls._obter_para_alterar(trecho_id)
            trecho.ativo = ativo
            trecho.atualizado_por = administrador
            trecho.save(update_fields=["ativo", "atualizado_por", "atualizado_em"])
        return trecho
