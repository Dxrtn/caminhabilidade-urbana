"""Consultas públicas (somente leitura): mapa, busca e detalhe do trecho.

O mapa e a busca leem a view do banco vw_trechos_mapa (model TrechoMapa), não a tabela trecho.
"""

from datetime import timedelta

from django.db.models import Prefetch, Q
from django.utils import timezone

from trechos.exceptions import TextoDeBuscaCurto, TrechoNaoEncontrado
from trechos.models import Classificacao, FotoTrecho, Obstaculo, Trecho, TrechoMapa, TrechoObstaculo
from trechos.services.dados import DetalheTrecho, FotoPublica, Relato

MINIMO_DA_BUSCA = 3
MAXIMO_DE_RESULTADOS = 5
MAXIMO_DE_RELATOS = 5
DIAS_PARA_DESATUALIZADO = 180


class TrechoConsultaService:
    @classmethod
    def listar_para_mapa(cls, classificacao: str | None = None, obstaculo_codigo: str | None = None) -> list[dict]:
        trechos = TrechoMapa.objects.order_by("logradouro", "id")
        if classificacao in Classificacao.values:  # valor inválido é ignorado
            trechos = trechos.filter(classificacao=classificacao)
        if obstaculo_codigo:
            com_obstaculo = TrechoObstaculo.objects.filter(obstaculo__codigo=obstaculo_codigo).values("trecho_id")
            trechos = trechos.filter(id__in=com_obstaculo)
        rotulos = dict(Classificacao.choices)
        return [
            {
                "id": t.id,
                "logradouro": t.logradouro,
                "bairro": t.bairro,
                "classificacao": t.classificacao,
                "classificacao_rotulo": rotulos.get(t.classificacao, t.classificacao),
                "coordenadas": [
                    [float(t.lat_inicio), float(t.lng_inicio)],
                    [float(t.lat_fim), float(t.lng_fim)],
                ],
                "feedbacks_em_analise": t.feedbacks_em_analise,
            }
            for t in trechos
        ]

    @classmethod
    def buscar(cls, texto: str | None) -> list[dict]:
        texto = (texto or "").strip()
        if len(texto.replace(" ", "")) < MINIMO_DA_BUSCA:
            raise TextoDeBuscaCurto()
        trechos = TrechoMapa.objects.filter(Q(logradouro__icontains=texto) | Q(bairro__icontains=texto)).order_by(
            "logradouro", "id"
        )[:MAXIMO_DE_RESULTADOS]
        return [
            {
                "id": t.id,
                "logradouro": t.logradouro,
                "bairro": t.bairro,
                "referencias": f"{t.referencia_inicio} → {t.referencia_fim}",
                "centro": [
                    (float(t.lat_inicio) + float(t.lat_fim)) / 2,
                    (float(t.lng_inicio) + float(t.lng_fim)) / 2,
                ],
            }
            for t in trechos
        ]

    @classmethod
    def listar_obstaculos(cls) -> list[Obstaculo]:
        return list(Obstaculo.objects.order_by("nome"))

    @classmethod
    def obter_detalhe(cls, trecho_id: int) -> DetalheTrecho:
        trecho = (
            Trecho.objects.select_related("bairro")
            .prefetch_related(Prefetch("fotos", queryset=FotoTrecho.objects.order_by("criado_em", "id")))
            .filter(pk=trecho_id, ativo=True)
            .first()
        )
        if trecho is None:
            raise TrechoNaoEncontrado()

        relatos, fotos_de_relatos = cls._relatos(trecho)
        fotos = [FotoPublica(url=f.imagem.url, descricao=f.descricao or f"Foto de {trecho.logradouro}") for f in trecho.fotos.all()]
        limite = timezone.now() - timedelta(days=DIAS_PARA_DESATUALIZADO)
        return DetalheTrecho(
            trecho=trecho,
            obstaculos=list(trecho.obstaculos.order_by("nome")),
            fotos=fotos + fotos_de_relatos,
            relatos=relatos,
            desatualizado=trecho.atualizado_em < limite,
        )

    @staticmethod
    def _relatos(trecho: Trecho) -> tuple[list[Relato], list[FotoPublica]]:
        # Única leitura de feedbacks a partir de trechos (exceção registrada em docs/arquitetura.md);
        # o import fica aqui dentro para evitar import circular.
        from feedbacks.models import Feedback, FotoFeedback, StatusFeedback

        aprovadas = Prefetch(
            "fotos", queryset=FotoFeedback.objects.filter(aprovada=True).order_by("criado_em", "id"), to_attr="aprovadas"
        )
        # Relatos rejeitados não são públicos: podem ter sido recusados por conteúdo impróprio.
        feedbacks = (
            Feedback.objects.filter(trecho=trecho)
            .exclude(status=StatusFeedback.REJEITADO)
            .prefetch_related(aprovadas)
            .order_by("-criado_em", "-id")[:MAXIMO_DE_RELATOS]
        )
        relatos = []
        for feedback in feedbacks:
            em_analise = feedback.status == StatusFeedback.EM_ANALISE
            fotos = [] if em_analise else [_foto_de_relato(f, trecho) for f in feedback.aprovadas]
            relatos.append(
                Relato(
                    tipo_rotulo=feedback.get_tipo_display(),
                    descricao=feedback.descricao,
                    data=feedback.criado_em,
                    em_analise=em_analise,
                    fotos=fotos,
                )
            )

        # Fotos públicas do trecho: as aprovadas de qualquer relato aceito, não só dos 5 últimos.
        todas_aprovadas = FotoFeedback.objects.filter(
            feedback__trecho=trecho, feedback__status=StatusFeedback.ACEITO, aprovada=True
        ).order_by("criado_em", "id")
        return relatos, [_foto_de_relato(f, trecho) for f in todas_aprovadas]


def _foto_de_relato(foto, trecho: Trecho) -> FotoPublica:
    return FotoPublica(url=foto.imagem.url, descricao=f"Foto enviada por um usuário em {trecho.logradouro}")
