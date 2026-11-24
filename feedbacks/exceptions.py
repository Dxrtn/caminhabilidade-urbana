"""Exceções de domínio da app feedbacks. As views as convertem em mensagens ou respostas HTTP."""


class FeedbackErro(Exception):
    mensagem = "Não foi possível concluir a operação com o feedback."

    def __init__(self, mensagem: str | None = None):
        super().__init__(mensagem or self.mensagem)


class LimiteDiarioAtingido(FeedbackErro):
    mensagem = "Você já enviou 10 feedbacks hoje. Tente de novo amanhã."


class FeedbackEmAnaliseExistente(FeedbackErro):
    mensagem = "Você já tem um feedback em análise sobre este trecho. Aguarde a análise ou exclua o anterior."


class FeedbackIncompleto(FeedbackErro):
    mensagem = "Para relatar um novo problema, marque ao menos 1 obstáculo e envie ao menos 1 foto."


class FotosEmExcesso(FeedbackErro):
    mensagem = "Envie no máximo 3 fotos."


class FeedbackNaoEncontrado(FeedbackErro):
    mensagem = "Feedback não encontrado."


class FeedbackNaoPodeSerExcluido(FeedbackErro):
    mensagem = "Este feedback já foi analisado e não pode mais ser excluído."
