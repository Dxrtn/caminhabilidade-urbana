from collections.abc import Iterable
from datetime import datetime, time
from decimal import Decimal

from django.core.files.uploadedfile import UploadedFile
from django.core.paginator import Page, Paginator
from django.db import IntegrityError, transaction
from django.utils import timezone

from comum.geo import distancia_em_metros
from feedbacks.exceptions import (
    FeedbackEmAnaliseExistente,
    FeedbackIncompleto,
    FeedbackNaoEncontrado,
    FeedbackNaoPodeSerExcluido,
    FotosEmExcesso,
    LimiteDiarioAtingido,
)
from feedbacks.models import Feedback, FeedbackObstaculo, FotoFeedback, StatusFeedback, TipoFeedback
from trechos.exceptions import TrechoNaoEncontrado
from trechos.models import Obstaculo, Trecho

LIMITE_DIARIO = 10
MAXIMO_DE_FOTOS = 3
DISTANCIA_MAXIMA_EM_METROS = 200
POR_PAGINA = 10
RESTRICAO_UM_EM_ANALISE = "uq_feedback_um_em_analise_por_trecho"


class FeedbackService:
    @classmethod
    def obter_trecho(cls, trecho_id: int) -> Trecho:
        """Trecho ativo que pode receber feedback."""
        trecho = Trecho.objects.select_related("bairro").filter(pk=trecho_id, ativo=True).first()
        if trecho is None:
            raise TrechoNaoEncontrado()
        return trecho

    @classmethod
    def enviar(
        cls,
        usuario,
        trecho_id: int,
        tipo: str,
        descricao: str,
        obstaculo_ids: Iterable[int] = (),
        classificacao_sugerida: str | None = None,
        fotos: Iterable[UploadedFile] = (),
        latitude: float | Decimal | None = None,
        longitude: float | Decimal | None = None,
    ) -> Feedback:
        obstaculo_ids = list(obstaculo_ids)
        fotos = list(fotos)

        # Verificações na ordem da spec.
        trecho = cls.obter_trecho(trecho_id)
        if cls._enviados_hoje(usuario) >= LIMITE_DIARIO:
            raise LimiteDiarioAtingido()
        if cls._tem_em_analise(usuario, trecho):
            raise FeedbackEmAnaliseExistente()
        if len(fotos) > MAXIMO_DE_FOTOS:
            raise FotosEmExcesso()
        if tipo == TipoFeedback.NOVO_PROBLEMA and (not obstaculo_ids or not fotos):
            raise FeedbackIncompleto()

        # A posição só serve para este cálculo: não é guardada (RF-23).
        a_distancia = cls._esta_longe(trecho, latitude, longitude)
        try:
            with transaction.atomic():
                feedback = Feedback.objects.create(
                    usuario=usuario,
                    trecho=trecho,
                    tipo=tipo,
                    descricao=descricao,
                    classificacao_sugerida=classificacao_sugerida or None,
                    enviado_a_distancia=a_distancia,
                )
                obstaculos = Obstaculo.objects.filter(pk__in=obstaculo_ids)
                FeedbackObstaculo.objects.bulk_create(
                    [FeedbackObstaculo(feedback=feedback, obstaculo=obstaculo) for obstaculo in obstaculos]
                )
                for foto in fotos:
                    FotoFeedback.objects.create(feedback=feedback, imagem=foto)
        except IntegrityError as exc:
            # Envio simultâneo: a constraint do banco garante 1 em análise por usuário e trecho.
            if _restricao_violada(exc) == RESTRICAO_UM_EM_ANALISE:
                raise FeedbackEmAnaliseExistente() from exc
            raise
        return feedback  # o trecho não é alterado (RF-22)

    @classmethod
    def listar_do_usuario(cls, usuario, pagina: int | str | None = 1) -> Page:
        feedbacks = Feedback.objects.filter(usuario=usuario).select_related("trecho").order_by("-criado_em", "-id")
        return Paginator(feedbacks, POR_PAGINA).get_page(pagina)

    @classmethod
    def excluir(cls, feedback_id: int, usuario) -> None:
        with transaction.atomic():
            # Filtra pelo dono na própria consulta: o de outra pessoa é "não encontrado".
            feedback = Feedback.objects.select_for_update().filter(pk=feedback_id, usuario=usuario).first()
            if feedback is None:
                raise FeedbackNaoEncontrado()
            if feedback.status != StatusFeedback.EM_ANALISE:
                raise FeedbackNaoPodeSerExcluido()
            arquivos = [(foto.imagem.storage, foto.imagem.name) for foto in feedback.fotos.all()]
            feedback.delete()  # obstáculos e fotos saem pelo ON DELETE CASCADE do banco
            # Os arquivos só saem do disco se a exclusão no banco for confirmada.
            for armazenamento, nome in arquivos:
                transaction.on_commit(lambda a=armazenamento, n=nome: a.delete(n))

    # ---------- auxiliares

    @staticmethod
    def _enviados_hoje(usuario) -> int:
        # "Hoje" no fuso do projeto (TIME_ZONE = America/Maceio).
        inicio_do_dia = timezone.make_aware(datetime.combine(timezone.localdate(), time.min))
        return Feedback.objects.filter(usuario=usuario, criado_em__gte=inicio_do_dia).count()

    @staticmethod
    def _tem_em_analise(usuario, trecho: Trecho) -> bool:
        return Feedback.objects.filter(usuario=usuario, trecho=trecho, status=StatusFeedback.EM_ANALISE).exists()

    @staticmethod
    def _esta_longe(trecho: Trecho, latitude, longitude) -> bool:
        if latitude is None or longitude is None:
            return False
        meio = ((trecho.lat_inicio + trecho.lat_fim) / 2, (trecho.lng_inicio + trecho.lng_fim) / 2)
        pontos = [(trecho.lat_inicio, trecho.lng_inicio), meio, (trecho.lat_fim, trecho.lng_fim)]
        mais_perto = min(distancia_em_metros(latitude, longitude, lat, lng) for lat, lng in pontos)
        return mais_perto > DISTANCIA_MAXIMA_EM_METROS


def _restricao_violada(exc: IntegrityError) -> str | None:
    return getattr(getattr(exc.__cause__, "diag", None), "constraint_name", None)
