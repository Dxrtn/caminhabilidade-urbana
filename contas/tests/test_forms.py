from django.test import SimpleTestCase

from contas.forms import CadastroForm

DADOS_VALIDOS = {
    "nome_completo": "Maria da Silva",
    "email": "maria@exemplo.com",
    "celular": "82987654321",
    "senha": "senhaforte1",
    "confirmacao_senha": "senhaforte1",
    "locomocao": "",
    "aceite_termos": "on",
}


def _form(**alteracoes) -> CadastroForm:
    return CadastroForm(data={**DADOS_VALIDOS, **alteracoes})


class CadastroFormTests(SimpleTestCase):
    def test_dados_validos_sao_aceitos_e_locomocao_vazia_vira_nao_informado(self):
        form = _form()

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["locomocao"], "NAO_INFORMADO")

    def test_senha_sem_numero_sem_letra_ou_curta_e_recusada(self):
        for senha in ["somenteletras", "12345678", "abc123"]:
            with self.subTest(senha=senha):
                form = _form(senha=senha, confirmacao_senha=senha)

                self.assertFalse(form.is_valid())
                self.assertIn("senha", form.errors)

    def test_senhas_diferentes_sao_recusadas(self):
        form = _form(confirmacao_senha="outrasenha2")

        self.assertFalse(form.is_valid())
        self.assertIn("As senhas não conferem.", form.errors["confirmacao_senha"])

    def test_celular_com_mascara_e_normalizado_para_11_digitos(self):
        form = _form(celular="(82) 98765-4321")

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["celular"], "82987654321")

    def test_celular_sem_o_9_e_recusado(self):
        form = _form(celular="(82) 8765-4321")

        self.assertFalse(form.is_valid())
        self.assertIn("celular", form.errors)

    def test_cadastro_sem_aceite_dos_termos_e_recusado(self):
        dados = {**DADOS_VALIDOS}
        del dados["aceite_termos"]

        form = CadastroForm(data=dados)

        self.assertFalse(form.is_valid())
        self.assertIn("aceite_termos", form.errors)
