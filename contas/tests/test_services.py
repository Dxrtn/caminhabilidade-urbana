from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from contas.exceptions import (
    CelularJaCadastrado,
    CodigoExpirado,
    CodigoInvalido,
    EmailJaCadastrado,
    LimiteDeReenvioAtingido,
)
from contas.services import CadastroService, EnviadorEmMemoria, EnviadorSmsSimulado, VerificacaoService

Usuario = get_user_model()

DADOS_CADASTRO = {
    "nome_completo": "Maria da Silva",
    "email": "maria@exemplo.com",
    "celular": "82987654321",
    "senha": "senhaforte1",
    "locomocao": "CADEIRA_DE_RODAS",
    "aceitou_termos": True,
}


@override_settings(ENVIADOR_DE_CODIGO="contas.services.enviadores.EnviadorEmMemoria")
class CadastroServiceTests(TestCase):
    def setUp(self):
        EnviadorEmMemoria.limpar()

    def test_cadastrar_cria_usuario_inativo_com_termos_e_envia_codigo(self):
        usuario = CadastroService.cadastrar(**DADOS_CADASTRO)

        self.assertFalse(usuario.is_active)
        self.assertFalse(usuario.celular_verificado)
        self.assertIsNotNone(usuario.termos_aceitos_em)
        codigo = usuario.codigos.get()
        self.assertEqual(EnviadorEmMemoria.enviados, [("82987654321", codigo.codigo)])

    def test_cadastrar_com_email_repetido_levanta_email_ja_cadastrado(self):
        CadastroService.cadastrar(**DADOS_CADASTRO)

        with self.assertRaises(EmailJaCadastrado):
            CadastroService.cadastrar(**{**DADOS_CADASTRO, "email": "MARIA@Exemplo.com", "celular": "82911112222"})

    def test_cadastrar_com_celular_repetido_levanta_celular_ja_cadastrado(self):
        CadastroService.cadastrar(**DADOS_CADASTRO)

        with self.assertRaises(CelularJaCadastrado):
            CadastroService.cadastrar(**{**DADOS_CADASTRO, "email": "outra@exemplo.com"})


@override_settings(ENVIADOR_DE_CODIGO="contas.services.enviadores.EnviadorEmMemoria")
class VerificacaoServiceTests(TestCase):
    def setUp(self):
        EnviadorEmMemoria.limpar()
        self.usuario = CadastroService.cadastrar(**DADOS_CADASTRO)
        self.codigo = self.usuario.codigos.get()

    def test_verificar_com_codigo_correto_ativa_o_usuario(self):
        usuario = VerificacaoService.verificar(self.usuario.pk, self.codigo.codigo)

        usuario.refresh_from_db()
        self.assertTrue(usuario.is_active)
        self.assertTrue(usuario.celular_verificado)
        self.codigo.refresh_from_db()
        self.assertIsNotNone(self.codigo.usado_em)

    def test_verificar_com_codigo_errado_levanta_codigo_invalido(self):
        errado = "000000" if self.codigo.codigo != "000000" else "111111"

        with self.assertRaises(CodigoInvalido):
            VerificacaoService.verificar(self.usuario.pk, errado)

    def test_verificar_com_codigo_vencido_levanta_codigo_expirado(self):
        passado = timezone.now() - timedelta(minutes=20)
        self.usuario.codigos.update(criado_em=passado, expira_em=passado + timedelta(minutes=10))

        with self.assertRaises(CodigoExpirado):
            VerificacaoService.verificar(self.usuario.pk, self.codigo.codigo)

    def test_reenviar_funciona_3_vezes_e_levanta_limite_na_quarta(self):
        for _ in range(3):
            VerificacaoService.reenviar(self.usuario.pk)

        with self.assertRaises(LimiteDeReenvioAtingido):
            VerificacaoService.reenviar(self.usuario.pk)
        self.assertEqual(self.usuario.codigos.count(), 4)
        self.assertEqual(len(EnviadorEmMemoria.enviados), 4)


class EnviadorSmsSimuladoTests(TestCase):
    def test_registra_o_codigo_no_logger_contas_sms(self):
        with self.assertLogs("contas.sms", level="INFO") as registro:
            EnviadorSmsSimulado().enviar("82999999999", "123456")

        self.assertIn("[SMS SIMULADO] Para (82) 99999-9999: seu código é 123456", registro.output[0])
