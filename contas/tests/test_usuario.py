from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

Usuario = get_user_model()

DADOS = {"nome_completo": "Maria da Silva", "celular": "82987654321"}


class UsuarioManagerTests(TestCase):
    def test_create_user_cria_usuario_inativo_e_nao_verificado(self):
        usuario = Usuario.objects.create_user("maria@exemplo.com", "senha-forte-123", **DADOS)

        self.assertFalse(usuario.is_active)
        self.assertFalse(usuario.celular_verificado)
        self.assertFalse(usuario.is_staff)
        self.assertTrue(usuario.check_password("senha-forte-123"))

    def test_create_superuser_cria_ativo_e_verificado(self):
        usuario = Usuario.objects.create_superuser("admin@exemplo.com", "senha-forte-123", **DADOS)

        self.assertTrue(usuario.is_active)
        self.assertTrue(usuario.celular_verificado)
        self.assertTrue(usuario.is_staff)
        self.assertTrue(usuario.is_superuser)

    def test_create_user_normaliza_o_dominio_do_email(self):
        usuario = Usuario.objects.create_user("maria@EXEMPLO.com", "senha-forte-123", **DADOS)

        self.assertEqual(usuario.email, "maria@exemplo.com")
        self.assertEqual(str(usuario), "maria@exemplo.com")


class UsuarioConstraintsTests(TestCase):
    def test_banco_rejeita_celular_fora_do_formato(self):
        # Sem o 9 depois do DDD: só a constraint do banco impede a gravação.
        with self.assertRaises(IntegrityError), transaction.atomic():
            Usuario.objects.create_user(
                "maria@exemplo.com", "senha-forte-123", nome_completo="Maria", celular="82187654321"
            )

    def test_banco_rejeita_usuario_ativo_sem_celular_verificado(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Usuario.objects.create_user("maria@exemplo.com", "senha-forte-123", is_active=True, **DADOS)
