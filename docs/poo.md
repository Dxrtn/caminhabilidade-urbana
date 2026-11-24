# Pilares de POO no projeto

Este arquivo mapeia onde cada pilar da orientação a objetos aparece no código. Ele guia a implementação e serve de roteiro para a apresentação. A IA atualiza a coluna "Onde está" sempre que criar ou alterar uma dessas classes (regra do `AGENTS.md`).

Status: **em implementação**. Os itens marcados com ✔ já existem no código (specs 0001 a 0007). Os demais caminhos ainda são planejados.

## Abstração

Esconder os detalhes e expor só o que importa, por meio de classes abstratas que definem um contrato.

| Classe | O que abstrai | Onde está | Spec |
|---|---|---|---|
| `EnviadorDeCodigo` (ABC) | "Enviar um código para um celular", sem dizer como. `enviar()` é `@abstractmethod`: a classe não pode ser instanciada, só as filhas | `contas/services/enviadores.py` ✔ | [0002](specs/0002-contas.md) |
| `ImportadorDeTrechos` (ABC) | "Importar trechos de uma origem", sem dizer qual. `ler()` é `@abstractmethod`; `importar()` é concreto e igual para todas as origens | `trechos/services/importadores.py` ✔ | [0004](specs/0004-gestao-de-trechos.md) |
| `ModeloComDatas` (abstract model) | Datas de criação e atualização de qualquer registro. Com `Meta.abstract = True`, não gera tabela: só empresta os campos às filhas | `comum/models/base.py` ✔ | [0001](specs/0001-fundacao.md) |

## Herança

Reaproveitar e especializar comportamento a partir de uma classe base.

| Classe filha | Classe base | O que herda | Onde está |
|---|---|---|---|
| `Trecho`, `Feedback` | `ModeloComDatas` | Campos `criado_em` e `atualizado_em`, sem repetir a declaração; a trigger e a view `vw_trechos_mapa` leem `trecho.atualizado_em` | `trechos/models/trecho.py` ✔, `feedbacks/models/feedback.py` ✔ |
| `SomenteLeituraAdmin` e seus filhos (`TrechoAdmin`, `HistoricoTrechoAdmin`, `FeedbackAdmin` etc.) | `ModelAdmin` (Django) | A tela do Admin; a classe base sobrescreve `has_add_permission`, `has_change_permission` e `has_delete_permission` para negar a escrita, e as filhas só declaram as colunas | `comum/admin.py` ✔, `trechos/admin.py` ✔, `feedbacks/admin.py` ✔ |
| `Usuario` | `AbstractUser` (Django) | Senha, permissões, `is_active`, `is_staff`. Especializa removendo `username`, `first_name` e `last_name`, usando o e-mail no login e sobrescrevendo `get_full_name()` e `get_short_name()`. O `UsuarioManager` herda de `BaseUserManager` e sobrescreve `create_user` e `create_superuser` | `contas/models/usuario.py` ✔ |
| `EnviadorSmsSimulado`, `EnviadorEmMemoria` | `EnviadorDeCodigo` | O contrato `enviar()`, que cada uma implementa do seu jeito. `EnviadorEmMemoria` também tem o atributo de classe `enviados` e o método de classe `limpar()` | `contas/services/enviadores.py` ✔ |
| `ImportadorDadosExemplo`, `ImportadorCsv` | `ImportadorDeTrechos` | O algoritmo completo de `importar()` e o atributo `_administrador`. `ImportadorCsv` estende o construtor com `super().__init__()` e sobrescreve também `_posicao()`, para os erros citarem a linha do arquivo | `trechos/services/importadores.py` ✔ |
| `AdministradorRequeridoMixin` | `LoginRequiredMixin` e `UserPassesTestMixin` | Herança múltipla: exige login **e** `is_staff`. Sobrescreve só `test_func()`; pela ordem de resolução (MRO), o login é verificado primeiro | `comum/mixins.py` ✔ |
| Todas as views | `django.views.View` | O despacho por método HTTP. Já existem `CadastroView`, `VerificarCelularView`, `ReenviarCodigoView`, `EntrarView`, `SairView` (com `LoginRequiredMixin`) e a `MapaView` provisória; o teste `comum/tests/test_arquitetura.py` garante a regra | `contas/views/` ✔, `trechos/views/` ✔, `feedbacks/views/` |
| `EntrarForm` | `AuthenticationForm` (Django) | Autenticação e mensagens de erro; sobrescreve `clean_username()` e o rótulo "E-mail" | `contas/forms/entrar.py` ✔ |
| Exceções de domínio | `ContaErro`, `TrechoErro`, `FeedbackErro` | Hierarquia de erros por app, cada filha sobrescrevendo só o atributo `mensagem`. Em contas: `EmailJaCadastrado`, `CelularJaCadastrado`, `CodigoInvalido`, `CodigoExpirado`, `LimiteDeReenvioAtingido` e `UsuarioNaoEncontrado`. Em trechos: `TrechoNaoEncontrado`, `TrechoDuplicado`, `DadosDeTrechoInvalidos` e `TextoDeBuscaCurto`. Em feedbacks: `LimiteDiarioAtingido`, `FeedbackEmAnaliseExistente`, `FeedbackIncompleto`, `FotosEmExcesso`, `FeedbackNaoEncontrado`, `FeedbackNaoPodeSerExcluido`, `FeedbackJaAnalisado` e `MotivoDeRejeicaoInvalido` | `contas/exceptions.py` ✔, `trechos/exceptions.py` ✔, `feedbacks/exceptions.py` ✔ |
| `CampoDeVariasImagens` | `forms.ImageField` (Django) | A validação de imagem com Pillow; sobrescreve `__init__` (limite de arquivos configurável) e `clean()`, que valida cada arquivo com o `clean()` da classe base. Usado pelo formulário de trecho (até 5) e pelo de feedback (limite no service) | `comum/forms.py` ✔ |

## Polimorfismo

O mesmo comando produz comportamentos diferentes conforme o objeto que o recebe.

| Chamada | Comportamentos | Onde está |
|---|---|---|
| `enviador.enviar(celular, codigo)` | No desenvolvimento, mostra no terminal; nos testes, guarda em memória. O `VerificacaoService.gerar_e_enviar()` não sabe qual recebeu: `obter_enviador()` cria a classe indicada em `settings.ENVIADOR_DE_CODIGO` | `contas/services/verificacao_service.py` ✔ |
| `except (CodigoInvalido, CodigoExpirado) as exc` | Uma cláusula trata os dois erros de código, e `str(exc)` mostra a mensagem própria de cada um | `contas/views/cadastro.py` ✔ |
| `importador.importar()` | Lê da lista de exemplo ou de um CSV. O comando `carregar_trechos` escolhe a subclasse e chama `importar()` sem saber qual é a origem | `trechos/management/commands/carregar_trechos.py` ✔ |
| `ler()` sobrescrito | Cada importador implementa a leitura da sua origem, e o `importar()` da classe base a chama (*Template Method*). O mesmo vale para `_posicao()`: "item 3" no exemplo, "linha 3" no CSV | `trechos/services/importadores.py` ✔ |
| `except (TrechoDuplicado, DadosDeTrechoInvalidos) as exc` | Uma cláusula trata os dois erros do formulário de trecho, e `str(exc)` mostra a mensagem de cada um | `trechos/views/painel.py` ✔ |
| `except FeedbackErro as exc` | Uma única cláusula trata qualquer erro de feedback (limite diário, em análise, incompleto, fotos em excesso), e `str(exc)` mostra a mensagem própria de cada um | `feedbacks/views/feedbacks.py` ✔ |

## Encapsulamento

Proteger o estado e as regras, expondo só uma interface pública.

| Onde | Como |
|---|---|
| Services | As views só chamam métodos públicos como `CadastroService.cadastrar(...)` ✔ e `FeedbackService.enviar(...)` ✔; a geração do código, o limite de reenvios, o limite diário, a regra de distância e a transação ficam escondidos dentro dos services (`contas/services/`, `feedbacks/services/`), em métodos internos como `_enviados_hoje()`, `_tem_em_analise()` e `_esta_longe()` |
| `ImportadorDeTrechos._administrador` ✔ | Atributo protegido, definido no construtor e usado só pela própria classe e subclasses; o mesmo para `_resultado` e, no `ImportadorCsv`, `_caminho` e `_linha` |
| `TrechoService` ✔ | As views do painel só chamam `criar`, `atualizar`, `desativar` etc.; a resolução do bairro, a verificação de duplicidade, a transação e o `select_for_update` ficam em métodos `_` internos (`_validar`, `_existe_igual`, `_obter_para_alterar`, `_definir_obstaculos`) |
| Métodos auxiliares com `_` | Ex.: `VerificacaoService._gerar_codigo()` ✔ e `CadastroService._garantir_disponivel()` ✔, de uso interno do service; `_distancia_ate_trecho()` (planejado) |
| Exceções de domínio | O service comunica falhas sem expor detalhes do banco. Em `CadastroService.cadastrar` ✔, o `IntegrityError` de um cadastro simultâneo vira `EmailJaCadastrado` ou `CelularJaCadastrado`; em `FeedbackService.enviar` ✔, o `IntegrityError` da constraint `uq_feedback_um_em_analise_por_trecho` vira `FeedbackEmAnaliseExistente` |
| `HistoricoTrecho` ✔ | Só a trigger `trg_trecho_historico` grava (`trechos/migrations/0003_trigger_historico_trecho.py`); no Admin é somente leitura, e nenhum service escreve nela |
| `TrechoMapa` ✔ | Lê a view `vw_trechos_mapa` com `managed = False`; `save()` e `delete()` são sobrescritos para levantar `NotSupportedError`, então o objeto não pode ser gravado (`trechos/models/trecho_mapa.py`) |
| `DadosTrecho` (`frozen=True`) ✔ | Objeto de dados imutável: depois de criado, não pode ser alterado (`trechos/services/dados.py`). O form e os importadores o criam, e o `TrechoService` só o lê |
| `DetalheTrecho`, `Relato`, `FotoPublica` (`frozen=True`) ✔ | Saída imutável do `TrechoConsultaService.obter_detalhe` (`trechos/services/dados.py`). `Relato` não tem campo de autor: a view e o template não têm como mostrar quem enviou o feedback (RF-15) |

| `AnaliseService` ✔ | As views da análise só chamam `aceitar` e `rejeitar`; a trava da linha (`select_for_update`), o controle de status, a chamada ao `TrechoService` e a notificação ficam nos métodos internos `_obter_em_analise()` e `_registrar_analise()` (`feedbacks/services/analise_service.py`) |
