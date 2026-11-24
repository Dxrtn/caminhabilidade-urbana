import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from contas.exceptions import (
    CodigoExpirado,
    CodigoInvalido,
    LimiteDeReenvioAtingido,
    UsuarioNaoEncontrado,
)
from contas.models import CodigoVerificacao, Usuario
from contas.services.enviadores import EnviadorDeCodigo, obter_enviador

VALIDADE_DO_CODIGO = timedelta(minutes=10)
MAXIMO_DE_CODIGOS = 4  # o primeiro envio mais 3 reenvios


class VerificacaoService:
    @classmethod
    def obter_pendente(cls, usuario_id: int | None) -> Usuario:
        """Usuário que ainda precisa verificar o celular."""
        usuario = get_user_model().objects.filter(pk=usuario_id, celular_verificado=False).first()
        if usuario is None:
            raise UsuarioNaoEncontrado()
        return usuario

    @classmethod
    def gerar_e_enviar(cls, usuario: Usuario, enviador: EnviadorDeCodigo | None = None) -> CodigoVerificacao:
        enviador = enviador or obter_enviador()
        agora = timezone.now()
        codigo = CodigoVerificacao.objects.create(
            usuario=usuario,
            codigo=cls._gerar_codigo(),
            criado_em=agora,
            expira_em=agora + VALIDADE_DO_CODIGO,
        )
        enviador.enviar(usuario.celular, codigo.codigo)
        return codigo

    @classmethod
    def verificar(cls, usuario_id: int | None, codigo: str) -> Usuario:
        with transaction.atomic():
            usuario = cls.obter_pendente(usuario_id)
            atual = (
                usuario.codigos.select_for_update()
                .filter(usado_em__isnull=True)
                .order_by("-criado_em")
                .first()
            )
            if atual is None or not secrets.compare_digest(atual.codigo, codigo):
                raise CodigoInvalido()
            agora = timezone.now()
            if atual.expira_em <= agora:
                raise CodigoExpirado()

            atual.usado_em = agora
            atual.save(update_fields=["usado_em"])
            usuario.celular_verificado = True
            usuario.is_active = True
            usuario.save(update_fields=["celular_verificado", "is_active"])
        return usuario

    @classmethod
    def reenviar(cls, usuario_id: int | None, enviador: EnviadorDeCodigo | None = None) -> CodigoVerificacao:
        usuario = cls.obter_pendente(usuario_id)
        if usuario.codigos.count() >= MAXIMO_DE_CODIGOS:
            raise LimiteDeReenvioAtingido()
        return cls.gerar_e_enviar(usuario, enviador)

    @staticmethod
    def _gerar_codigo() -> str:
        return f"{secrets.randbelow(10**6):06d}"
