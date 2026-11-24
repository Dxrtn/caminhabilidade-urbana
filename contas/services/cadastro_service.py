from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

from contas.exceptions import CelularJaCadastrado, EmailJaCadastrado
from contas.models import Locomocao, Usuario
from contas.services.enviadores import EnviadorDeCodigo
from contas.services.verificacao_service import VerificacaoService


class CadastroService:
    @classmethod
    def cadastrar(
        cls,
        *,
        nome_completo: str,
        email: str,
        celular: str,
        senha: str,
        locomocao: str = Locomocao.NAO_INFORMADO,
        aceitou_termos: bool,
        enviador: EnviadorDeCodigo | None = None,
    ) -> Usuario:
        if not aceitou_termos:
            raise ValueError("O cadastro exige o aceite dos termos de uso.")

        # Guardado em minúsculas para que a unicidade e o login não dependam da caixa.
        email = email.strip().lower()
        cls._garantir_disponivel(email, celular)

        try:
            with transaction.atomic():
                usuario = get_user_model().objects.create_user(
                    email,
                    senha,
                    nome_completo=nome_completo,
                    celular=celular,
                    locomocao=locomocao,
                    termos_aceitos_em=timezone.now(),
                )
                VerificacaoService.gerar_e_enviar(usuario, enviador)
        except IntegrityError:
            # Outro cadastro gravou o mesmo e-mail ou celular entre a verificação e o INSERT.
            cls._garantir_disponivel(email, celular)
            raise
        return usuario

    @staticmethod
    def _garantir_disponivel(email: str, celular: str) -> None:
        usuarios = get_user_model().objects
        if usuarios.filter(email__iexact=email).exists():
            raise EmailJaCadastrado()
        if usuarios.filter(celular=celular).exists():
            raise CelularJaCadastrado()
