# Spec 0002: Contas — cadastro, verificação e autenticação

- **Status:** Proposto
- **Requisitos:** RF-01 a RF-08 do [PRD 0001](../prd/0001-caminhabilidade-urbana.md)
- **Decisões:** [ADR 0002](../adr/0002-usuario-customizado-com-login-por-email.md), [ADR 0005](../adr/0005-sms-simulado.md)
- **Depende de:** [Spec 0001](0001-fundacao.md)

## Model `CodigoVerificacao` (`contas/models/codigo_verificacao.py`)

| Campo | Tipo | Regras |
|---|---|---|
| `usuario` | `ForeignKey(Usuario, on_delete=models.DB_CASCADE, related_name="codigos")` | Obrigatório |
| `codigo` | `CharField(max_length=6)` | 6 dígitos, gerado com `secrets` |
| `criado_em` | `DateTimeField(default=timezone.now)` | |
| `expira_em` | `DateTimeField` | `criado_em` + 10 minutos |
| `usado_em` | `DateTimeField(null=True, blank=True)` | Preenchido ao verificar |

- `Meta.db_table = "codigo_verificacao"`.
- Constraints: `ck_codigo_seis_digitos` (`^[0-9]{6}$`) e `ck_codigo_expira_depois_de_criado` (`expira_em > criado_em`).

## Envio do código: abstração e polimorfismo (`contas/services/enviadores.py`)

```python
class EnviadorDeCodigo(ABC):
    @abstractmethod
    def enviar(self, celular: str, codigo: str) -> None: ...
```

| Classe | Comportamento |
|---|---|
| `EnviadorSmsSimulado(EnviadorDeCodigo)` | Registra no logger `contas.sms` e exibe no terminal: `[SMS SIMULADO] Para (82) 99999-9999: seu código é 123456`. O celular aparece formatado |
| `EnviadorEmMemoria(EnviadorDeCodigo)` | Guarda `(celular, codigo)` em uma lista da classe, `enviados`, com o método de classe `limpar()`. Usado nos testes |

`obter_enviador() -> EnviadorDeCodigo` instancia a classe indicada em `settings.ENVIADOR_DE_CODIGO` com `import_string`. Os testes usam `@override_settings(ENVIADOR_DE_CODIGO="contas.services.enviadores.EnviadorEmMemoria")`.

Os services abaixo dependem apenas de `EnviadorDeCodigo` e nunca verificam qual subclasse receberam.

## Exceções (`contas/exceptions.py`)

Todas herdam de `ContaErro(Exception)` e têm uma mensagem amigável em português:

`EmailJaCadastrado`, `CelularJaCadastrado`, `CodigoInvalido`, `CodigoExpirado`, `LimiteDeReenvioAtingido`, `UsuarioNaoEncontrado`.

## `CadastroService`

| Método | Regra |
|---|---|
| `cadastrar(nome_completo, email, celular, senha, locomocao, aceitou_termos, enviador=None) -> Usuario` | Em `transaction.atomic()`: levanta `EmailJaCadastrado` ou `CelularJaCadastrado` se já existirem (e-mail comparado sem diferenciar maiúsculas); cria o usuário inativo com `create_user`; preenche `termos_aceitos_em`; gera e envia o primeiro código com `VerificacaoService`. `aceitou_termos` falso levanta `ValueError` (o form já impede) |

## `VerificacaoService`

| Método | Regra |
|---|---|
| `gerar_e_enviar(usuario, enviador=None) -> CodigoVerificacao` | Cria um código de 6 dígitos com `secrets.randbelow(10**6)`, válido por 10 minutos, e chama `enviador.enviar(usuario.celular, codigo)`. Sem `enviador`, usa `obter_enviador()` |
| `verificar(usuario_id, codigo) -> Usuario` | Busca o código não usado mais recente do usuário. Código diferente: `CodigoInvalido`. Vencido: `CodigoExpirado`. Correto: marca `usado_em` e torna o usuário ativo e verificado, em `transaction.atomic()` |
| `reenviar(usuario_id, enviador=None) -> CodigoVerificacao` | Permite no máximo 3 reenvios, ou seja, 4 códigos no total por usuário. Acima disso: `LimiteDeReenvioAtingido` |

Usuário inexistente ou já verificado levanta `UsuarioNaoEncontrado`.

## Forms (`contas/forms/`)

- `CadastroForm(forms.Form)`: `nome_completo`, `email`, `celular`, `senha`, `confirmacao_senha`, `locomocao` (opcional, padrão `NAO_INFORMADO`) e `aceite_termos` (`BooleanField`, obrigatório).
  - `clean_celular`: remove tudo que não for dígito e exige 11 dígitos, com o terceiro igual a 9. Mensagem: "Informe o celular com DDD, ex.: (82) 99999-9999."
  - `clean_senha`: 8 a 64 caracteres, ao menos uma letra e um número.
  - `clean`: confirmação igual à senha ("As senhas não conferem.").
  - Rótulos visíveis em todos os campos; `autocomplete` adequado (`email`, `tel`, `new-password`) e `inputmode="tel"` no celular.
- `VerificacaoForm`: `codigo` com 6 dígitos, `inputmode="numeric"` e `autocomplete="one-time-code"`.
- `EntrarForm(AuthenticationForm)`: rótulo do campo de usuário "E-mail".

## Rotas (`app_name = "contas"`)

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/cadastro/` | `contas:cadastro` | `CadastroView` | GET, POST | Visitante |
| `/cadastro/verificar/` | `contas:verificar` | `VerificarCelularView` | GET, POST | Cadastro pendente |
| `/cadastro/reenviar/` | `contas:reenviar` | `ReenviarCodigoView` | POST | Cadastro pendente |
| `/entrar/` | `contas:entrar` | `EntrarView` | GET, POST | Público |
| `/sair/` | `contas:sair` | `SairView` | POST | Autenticado |

## Comportamento

### `CadastroView`

- **GET:** exibe o `CadastroForm`. Usuário autenticado é redirecionado ao mapa.
- **POST válido:** chama `CadastroService.cadastrar`, guarda o id na sessão (`cadastro_pendente_id`) e redireciona para `contas:verificar` com a mensagem "Enviamos um código para o seu celular."
- **POST com e-mail ou celular repetido:** exibe o formulário com o erro no campo correspondente.

### `VerificarCelularView`

- Sem `cadastro_pendente_id` na sessão: redireciona para o cadastro.
- **GET:** exibe o `VerificacaoForm` e o celular parcialmente oculto (`(82) 9****-9999`).
- **POST válido:** chama `VerificacaoService.verificar`, remove o id da sessão, faz `login()` e redireciona ao mapa com "Conta verificada. Bem-vindo(a)!".
- **Código inválido ou vencido:** exibe o formulário com a mensagem da exceção.

### `ReenviarCodigoView`

- **POST:** chama `VerificacaoService.reenviar` e volta para a verificação com "Código reenviado." ou com a mensagem de `LimiteDeReenvioAtingido`.

### `EntrarView`

- **GET:** exibe o `EntrarForm`. Usuário autenticado é redirecionado ao mapa.
- **POST válido:** `login()` e redireciona para `next`, se for seguro (`url_has_allowed_host_and_scheme`), ou ao mapa.
- **POST inválido:** mensagem padrão, sem revelar se o e-mail existe. Contas inativas não entram (comportamento padrão do `ModelBackend`).

### `SairView`

- **POST:** `logout()` e redireciona ao mapa. **GET:** 405.

Templates: `contas/cadastro.html`, `contas/verificar.html`, `contas/entrar.html`. A página de cadastro tem o link "Termos de uso" para uma seção simples no próprio template (texto curto informando a finalidade dos dados e que a localização não é armazenada).

## Testes

### Services

- [ ] `cadastrar` cria usuário inativo, com `termos_aceitos_em` preenchido, e envia um código pelo `EnviadorEmMemoria`.
- [ ] `cadastrar` com e-mail repetido (inclusive com maiúsculas diferentes) levanta `EmailJaCadastrado`.
- [ ] `cadastrar` com celular repetido levanta `CelularJaCadastrado`.
- [ ] `verificar` com o código correto ativa o usuário; com código errado levanta `CodigoInvalido`; com código vencido levanta `CodigoExpirado`.
- [ ] `reenviar` funciona 3 vezes e levanta `LimiteDeReenvioAtingido` na quarta.
- [ ] `EnviadorSmsSimulado` registra o código no logger `contas.sms` (`assertLogs`).

### Forms

- [ ] Senha sem número, sem letra ou com menos de 8 caracteres é recusada.
- [ ] Celular com máscara é normalizado para 11 dígitos; celular sem o 9 é recusado.
- [ ] Cadastro sem aceite dos termos é recusado.

### Views

- [ ] Cadastro válido redireciona para a verificação, e a verificação correta autentica o usuário.
- [ ] `/cadastro/verificar/` sem cadastro pendente redireciona para o cadastro.
- [ ] Conta não verificada não consegue entrar.
- [ ] `next` externo é ignorado no login.
- [ ] POST em `/sair/` encerra a sessão, e GET retorna 405.
