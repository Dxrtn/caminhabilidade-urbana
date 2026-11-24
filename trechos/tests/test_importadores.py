import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import CommandError, call_command
from django.test import TestCase

from trechos.dados_exemplo import TRECHOS_EXEMPLO
from trechos.models import Trecho
from trechos.services import ImportadorCsv, ImportadorDadosExemplo
from trechos.tests.fabrica import criar_usuario

CSV = """logradouro;bairro;referencia_inicio;referencia_fim;lado;lat_inicio;lng_inicio;lat_fim;lng_fim;classificacao;obstaculos;observacoes
Rua Um;Centro;Esquina A;Esquina B;PAR;-9.665800;-35.735300;-9.666500;-35.736000;ACESSIVEL;;Tudo certo.
Rua Dois;Bairro Inventado;Esquina A;Esquina B;IMPAR;-9.665800;-35.735300;-9.666500;-35.736000;PARCIAL;buraco;
Rua Três;Centro;Esquina C;Esquina D;UNICO;-9,667000;-35,737000;-9,667800;-35,737500;INACESSIVEL;degrau,obra;Obra na calçada.
Rua Quatro;Centro;Esquina E;Esquina F;PAR;abc;-35.737000;-9.667800;-35.737500;;;
"""


class ImportadorDadosExemploTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.administrador = criar_usuario(is_staff=True)

    def test_importa_todos_e_rodar_de_novo_so_gera_ignorados(self):
        primeira = ImportadorDadosExemplo(self.administrador).importar()

        self.assertEqual(primeira.erros, [])
        self.assertEqual(primeira.importados, len(TRECHOS_EXEMPLO))
        self.assertTrue(30 <= len(TRECHOS_EXEMPLO) <= 40)

        segunda = ImportadorDadosExemplo(self.administrador).importar()

        self.assertEqual((segunda.importados, segunda.ignorados, segunda.erros), (0, len(TRECHOS_EXEMPLO), []))
        self.assertEqual(Trecho.objects.count(), len(TRECHOS_EXEMPLO))

    def test_dados_de_exemplo_ficam_nos_tres_bairros_pedidos(self):
        self.assertEqual({t.bairro for t in TRECHOS_EXEMPLO}, {"Pajuçara", "Ponta Verde", "Jatiúca"})


class ImportadorCsvTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.administrador = criar_usuario(is_staff=True)

    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.caminho = Path(pasta.name) / "trechos.csv"
        self.caminho.write_text(CSV, encoding="utf-8")

    def test_importa_linhas_validas_e_relata_as_invalidas_sem_parar(self):
        resultado = ImportadorCsv(self.administrador, self.caminho).importar()

        self.assertEqual(resultado.importados, 2)
        self.assertEqual(len(resultado.erros), 2)
        self.assertIn("linha 3: Bairro 'Bairro Inventado' não existe.", resultado.erros)
        self.assertIn("linha 5: lat_inicio 'abc' não é um número.", resultado.erros)
        tres = Trecho.objects.get(logradouro="Rua Três")
        self.assertEqual(set(tres.obstaculos.values_list("codigo", flat=True)), {"degrau", "obra"})


class CarregarTrechosCommandTests(TestCase):
    def test_falha_sem_gravar_quando_admin_nao_e_administrador(self):
        comum = criar_usuario()

        with self.assertRaises(CommandError):
            call_command("carregar_trechos", "--exemplo", "--admin", comum.email, stdout=StringIO())

        self.assertFalse(Trecho.objects.exists())

    def test_exibe_o_resumo(self):
        administrador = criar_usuario(is_staff=True)
        saida = StringIO()

        call_command("carregar_trechos", "--exemplo", "--admin", administrador.email, stdout=saida)

        self.assertIn(f"Importados: {len(TRECHOS_EXEMPLO)}", saida.getvalue())
        self.assertIn("Ignorados (já existiam): 0", saida.getvalue())
