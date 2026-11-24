"""Exceções de domínio da app contas. As views as convertem em mensagens ou respostas HTTP."""


class ContaErro(Exception):
    mensagem = "Não foi possível concluir a operação com a conta."

    def __init__(self, mensagem: str | None = None):
        super().__init__(mensagem or self.mensagem)


class EmailJaCadastrado(ContaErro):
    mensagem = "Já existe uma conta com este e-mail."


class CelularJaCadastrado(ContaErro):
    mensagem = "Já existe uma conta com este celular."


class CodigoInvalido(ContaErro):
    mensagem = "Código incorreto. Confira o SMS e tente de novo."


class CodigoExpirado(ContaErro):
    mensagem = "Este código venceu. Peça um novo código."


class LimiteDeReenvioAtingido(ContaErro):
    mensagem = "Você atingiu o limite de reenvios do código."


class UsuarioNaoEncontrado(ContaErro):
    mensagem = "Cadastro pendente não encontrado. Faça o cadastro novamente."
