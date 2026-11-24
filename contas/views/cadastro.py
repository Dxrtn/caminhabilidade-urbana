from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.views import View

from contas.exceptions import (
    CelularJaCadastrado,
    CodigoExpirado,
    CodigoInvalido,
    EmailJaCadastrado,
    LimiteDeReenvioAtingido,
    UsuarioNaoEncontrado,
)
from contas.forms import CadastroForm, VerificacaoForm
from contas.services import CadastroService, VerificacaoService, mascarar_celular

CHAVE_CADASTRO_PENDENTE = "cadastro_pendente_id"


class CadastroView(View):
    template_name = "contas/cadastro.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("trechos:mapa")
        return render(request, self.template_name, {"form": CadastroForm()})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("trechos:mapa")
        form = CadastroForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        dados = form.cleaned_data
        try:
            usuario = CadastroService.cadastrar(
                nome_completo=dados["nome_completo"],
                email=dados["email"],
                celular=dados["celular"],
                senha=dados["senha"],
                locomocao=dados["locomocao"],
                aceitou_termos=dados["aceite_termos"],
            )
        except EmailJaCadastrado as exc:
            form.add_error("email", str(exc))
            return render(request, self.template_name, {"form": form})
        except CelularJaCadastrado as exc:
            form.add_error("celular", str(exc))
            return render(request, self.template_name, {"form": form})

        request.session[CHAVE_CADASTRO_PENDENTE] = usuario.pk
        messages.success(request, "Enviamos um código para o seu celular.")
        return redirect("contas:verificar")


class VerificarCelularView(View):
    template_name = "contas/verificar.html"

    def get(self, request):
        try:
            usuario = VerificacaoService.obter_pendente(request.session.get(CHAVE_CADASTRO_PENDENTE))
        except UsuarioNaoEncontrado:
            return _voltar_ao_cadastro(request)
        return self._exibir(request, VerificacaoForm(), usuario.celular)

    def post(self, request):
        usuario_id = request.session.get(CHAVE_CADASTRO_PENDENTE)
        try:
            pendente = VerificacaoService.obter_pendente(usuario_id)
        except UsuarioNaoEncontrado:
            return _voltar_ao_cadastro(request)

        form = VerificacaoForm(request.POST)
        if not form.is_valid():
            return self._exibir(request, form, pendente.celular)
        try:
            usuario = VerificacaoService.verificar(usuario_id, form.cleaned_data["codigo"])
        except (CodigoInvalido, CodigoExpirado) as exc:
            form.add_error("codigo", str(exc))
            return self._exibir(request, form, pendente.celular)

        request.session.pop(CHAVE_CADASTRO_PENDENTE, None)
        login(request, usuario)
        messages.success(request, "Conta verificada. Bem-vindo(a)!")
        return redirect("trechos:mapa")

    def _exibir(self, request, form, celular: str):
        contexto = {"form": form, "celular_mascarado": mascarar_celular(celular)}
        return render(request, self.template_name, contexto)


class ReenviarCodigoView(View):
    def post(self, request):
        try:
            VerificacaoService.reenviar(request.session.get(CHAVE_CADASTRO_PENDENTE))
        except UsuarioNaoEncontrado:
            return _voltar_ao_cadastro(request)
        except LimiteDeReenvioAtingido as exc:
            messages.error(request, str(exc))
            return redirect("contas:verificar")
        messages.success(request, "Código reenviado.")
        return redirect("contas:verificar")


def _voltar_ao_cadastro(request):
    request.session.pop(CHAVE_CADASTRO_PENDENTE, None)
    return redirect("contas:cadastro")
