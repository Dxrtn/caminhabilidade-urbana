# Pilares de POO no projeto

Este arquivo mapeia onde cada pilar da orientação a objetos aparece no código. Ele guia a implementação e serve de roteiro para a apresentação. A IA atualiza a coluna "Onde está" sempre que criar ou alterar uma dessas classes (regra do `AGENTS.md`).

Status: **em implementação**. Confirmados até a spec 0001 (marcados com ✔): `ModeloComDatas`, `Usuario` e `AdministradorRequeridoMixin`. Os demais caminhos ainda são planejados.

## Abstração

Esconder os detalhes e expor só o que importa, por meio de classes abstratas que definem um contrato.

| Classe | O que abstrai | Onde está | Spec |
|---|---|---|---|
| `EnviadorDeCodigo` (ABC) | "Enviar um código para um celular", sem dizer como | `contas/services/enviadores.py` | [0002](specs/0002-contas.md) |
| `ImportadorDeTrechos` (ABC) | "Importar trechos de uma origem", sem dizer qual | `trechos/services/importadores.py` | [0004](specs/0004-gestao-de-trechos.md) |
| `ModeloComDatas` (abstract model) | Datas de criação e atualização de qualquer registro. Com `Meta.abstract = True`, não gera tabela: só empresta os campos às filhas | `comum/models/base.py` ✔ | [0001](specs/0001-fundacao.md) |

## Herança

Reaproveitar e especializar comportamento a partir de uma classe base.

| Classe filha | Classe base | O que herda | Onde está |
|---|---|---|---|
| `Trecho`, `Feedback` | `ModeloComDatas` | Campos `criado_em` e `atualizado_em` | `trechos/models/`, `feedbacks/models/` |
| `Usuario` | `AbstractUser` (Django) | Senha, permissões, `is_active`, `is_staff`. Especializa removendo `username`, `first_name` e `last_name`, usando o e-mail no login e sobrescrevendo `get_full_name()` e `get_short_name()`. O `UsuarioManager` herda de `BaseUserManager` e sobrescreve `create_user` e `create_superuser` | `contas/models/usuario.py` ✔ |
| `EnviadorSmsSimulado`, `EnviadorEmMemoria` | `EnviadorDeCodigo` | O contrato `enviar()` | `contas/services/enviadores.py` |
| `ImportadorDadosExemplo`, `ImportadorCsv` | `ImportadorDeTrechos` | O algoritmo completo de `importar()` | `trechos/services/importadores.py` |
| `AdministradorRequeridoMixin` | `LoginRequiredMixin` e `UserPassesTestMixin` | Herança múltipla: exige login **e** `is_staff`. Sobrescreve só `test_func()`; pela ordem de resolução (MRO), o login é verificado primeiro | `comum/mixins.py` ✔ |
| Todas as views | `django.views.View` | O despacho por método HTTP | `*/views/` |
| Exceções de domínio | `ContaErro`, `TrechoErro`, `FeedbackErro` | Hierarquia de erros por app | `*/exceptions.py` |

## Polimorfismo

O mesmo comando produz comportamentos diferentes conforme o objeto que o recebe.

| Chamada | Comportamentos | Onde está |
|---|---|---|
| `enviador.enviar(celular, codigo)` | No desenvolvimento, mostra no terminal; nos testes, guarda em memória. O `VerificacaoService` não sabe qual recebeu | `contas/services/verificacao_service.py` |
| `importador.importar()` | Lê da lista de exemplo ou de um CSV. O comando `carregar_trechos` não sabe qual é a origem | `trechos/management/commands/carregar_trechos.py` |
| `ler()` sobrescrito | Cada importador implementa a leitura da sua origem, e o `importar()` da classe base a chama (*Template Method*) | `trechos/services/importadores.py` |
| `except FeedbackErro` | Uma única cláusula trata qualquer erro de feedback, cada um com sua mensagem | `feedbacks/views/` |

## Encapsulamento

Proteger o estado e as regras, expondo só uma interface pública.

| Onde | Como |
|---|---|
| Services | As views só chamam métodos públicos como `FeedbackService.enviar(...)`; o limite diário, a regra de distância e a transação ficam escondidos dentro do service |
| `ImportadorDeTrechos._administrador` | Atributo protegido, definido no construtor e usado só pela própria classe e subclasses |
| Métodos auxiliares com `_` | Ex.: `_gerar_codigo()`, `_distancia_ate_trecho()`, de uso interno do service |
| Exceções de domínio | O service comunica falhas sem expor detalhes do banco (o `IntegrityError` vira `FeedbackEmAnaliseExistente`) |
| `HistoricoTrecho` | Só a trigger do banco grava; o código não tem como alterar o histórico |
| `DadosTrecho` (`frozen=True`) | Objeto de dados imutável: depois de criado, não pode ser alterado |
