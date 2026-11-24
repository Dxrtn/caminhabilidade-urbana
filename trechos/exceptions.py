"""Exceções de domínio da app trechos. As views as convertem em mensagens ou respostas HTTP."""


class TrechoErro(Exception):
    mensagem = "Não foi possível concluir a operação com o trecho."

    def __init__(self, mensagem: str | None = None):
        super().__init__(mensagem or self.mensagem)


class TrechoNaoEncontrado(TrechoErro):
    mensagem = "Trecho não encontrado."


class TrechoDuplicado(TrechoErro):
    mensagem = "Já existe um trecho com este logradouro, estas referências e este lado."


class DadosDeTrechoInvalidos(TrechoErro):
    mensagem = "Os dados do trecho são inválidos."


class TextoDeBuscaCurto(TrechoErro):
    mensagem = "Digite ao menos 3 letras."
