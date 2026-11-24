# Spec 0006: Envio e acompanhamento de feedbacks

- **Status:** Implementado
- **Requisitos:** RF-18 a RF-26 do [PRD 0001](../prd/0001-caminhabilidade-urbana.md)
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-service.md), [ADR 0007](../adr/0007-regras-de-integridade-no-banco.md)
- **Depende de:** [Spec 0002](0002-contas.md), [Spec 0005](0005-mapa-e-detalhes.md)

## Exceções (`feedbacks/exceptions.py`)

Herdam de `FeedbackErro(Exception)`, com mensagens amigáveis:

| Exceção | Quando |
|---|---|
| `LimiteDiarioAtingido` | 10 feedbacks já enviados hoje (fuso `America/Maceio`) |
| `FeedbackEmAnaliseExistente` | O usuário já tem um feedback em análise no trecho |
| `FeedbackIncompleto` | "Novo problema" sem obstáculo ou sem foto |
| `FotosEmExcesso` | Mais de 3 fotos |
| `FeedbackNaoEncontrado` | Não existe ou é de outro usuário |
| `FeedbackNaoPodeSerExcluido` | Já foi analisado |

## `FeedbackService` (`feedbacks/services/feedback_service.py`)

| Método | Regra |
|---|---|
| `enviar(usuario, trecho_id, tipo, descricao, obstaculo_ids=(), classificacao_sugerida=None, fotos=(), latitude=None, longitude=None) -> Feedback` | Verificações, nesta ordem: trecho ativo (senão `TrechoNaoEncontrado`); limite diário; feedback em análise existente; mais de 3 fotos; "Novo problema" completo. Calcula `enviado_a_distancia` com `comum.geo.distancia_em_metros` até o ponto mais próximo entre início, meio e fim do trecho (> 200 m). Sem latitude/longitude, fica falso. **Não guarda** latitude nem longitude. Grava feedback, obstáculos e fotos em `transaction.atomic()`. Um `IntegrityError` da constraint `uq_feedback_um_em_analise_por_trecho` (envio simultâneo) é convertido em `FeedbackEmAnaliseExistente`. Não altera o trecho (RF-22) |
| `listar_do_usuario(usuario, pagina=1) -> Page` | 10 por página, mais recentes primeiro, com `select_related("trecho")` |
| `excluir(feedback_id, usuario)` | Só o dono (senão `FeedbackNaoEncontrado`) e só em análise (senão `FeedbackNaoPodeSerExcluido`). Apaga também as fotos do disco |

## `NotificacaoService` (`feedbacks/services/notificacao_service.py`)

| Método | Regra |
|---|---|
| `notificar(feedback, mensagem)` | Cria a notificação para o autor do feedback, se ele ainda existir |
| `contar_nao_lidas(usuario) -> int` | |
| `listar_recentes(usuario, limite=10)` | |
| `marcar_todas_como_lidas(usuario)` | |

Um *context processor* (`feedbacks/context_processors.py`) chama `contar_nao_lidas` para usuários autenticados e expõe `notificacoes_nao_lidas` ao `base.html`, que mostra o número ao lado de "Meus feedbacks".

## Form (`feedbacks/forms/feedback_form.py`)

`FeedbackForm(forms.Form)`:

- `tipo`: botões de opção (radio).
- `obstaculos`: checkboxes com o catálogo.
- `classificacao_sugerida`: select opcional, só com as três classificações avaliadas.
- `descricao`: textarea de 10 a 500 caracteres, com contador de caracteres em JavaScript.
- `fotos`: seleção múltipla, `accept="image/*"` e `capture="environment"` (abre a câmera no celular); cada imagem validada pelo Pillow, até 5 MB. Usa `comum.forms.CampoDeVariasImagens`, o mesmo campo do formulário de trecho, sem limite de quantidade no form: o limite de 3 é do service (`FotosEmExcesso`).
- `latitude` e `longitude`: campos ocultos, preenchidos por JavaScript apenas se o usuário permitir a localização.

A validação de "Novo problema exige obstáculo e foto" fica no service; o form só valida formato.

## Rotas (`app_name = "feedbacks"`)

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/trechos/<int:trecho_id>/feedback/` | `feedbacks:enviar` | `FeedbackCreateView` | GET, POST | Usuário |
| `/meus-feedbacks/` | `feedbacks:meus` | `MeusFeedbacksView` | GET | Usuário |
| `/meus-feedbacks/<int:feedback_id>/excluir/` | `feedbacks:excluir` | `FeedbackExcluirView` | POST | Dono |

## Comportamento

### `FeedbackCreateView`

- Usa `LoginRequiredMixin`. **GET:** formulário com o nome do trecho no topo (dados vindos do service; trecho inativo ou inexistente → 404) e um aviso: "Sua localização é usada apenas para conferir se você está perto do trecho e não é guardada."
- **POST válido:** chama `FeedbackService.enviar` e redireciona para o detalhe do trecho com "Feedback enviado! Ele será analisado pela nossa equipe."
- **Exceção de domínio:** reexibe o formulário com a mensagem da exceção, mantendo os dados digitados.
- Depois desta spec, o botão "Enviar feedback" passa a aparecer no detalhe do trecho ([spec 0005](0005-mapa-e-detalhes.md)).

### `MeusFeedbacksView`

- Lista paginada com trecho (link para o detalhe), data, tipo, status em texto e, se rejeitado, o motivo.
- Acima da lista, as notificações recentes. Ao abrir a página, marca todas como lidas.
- Feedbacks em análise têm o botão "Excluir" (POST com confirmação).

### `FeedbackExcluirView`

- **POST:** chama o service. `FeedbackNaoEncontrado` → 404; `FeedbackNaoPodeSerExcluido` → mensagem de erro. Sucesso → "Feedback excluído." **GET:** 405.

## Testes

### Service

- [x] `enviar` cria o feedback em análise com obstáculos e fotos e não altera a classificação do trecho.
- [x] "Novo problema" sem foto ou sem obstáculo levanta `FeedbackIncompleto`.
- [x] O 11º feedback do dia levanta `LimiteDiarioAtingido`.
- [x] Um segundo feedback em análise no mesmo trecho levanta `FeedbackEmAnaliseExistente`.
- [x] Mais de 3 fotos levanta `FotosEmExcesso`.
- [x] Posição a mais de 200 m marca `enviado_a_distancia`; a menos de 200 m ou sem posição, não. Nenhum campo guarda a posição.
- [x] Feedback para trecho inativo levanta `TrechoNaoEncontrado`.
- [x] `excluir` funciona para o dono em análise, levanta `FeedbackNaoEncontrado` para outro usuário e `FeedbackNaoPodeSerExcluido` para feedback já analisado.
- [x] `NotificacaoService` conta e marca notificações como lidas.

### Views

- [x] Visitante é redirecionado ao login ao abrir o formulário e ao abrir "Meus feedbacks".
- [x] Envio válido com imagem de teste (gerada pelo Pillow em memória) redireciona para o detalhe com a mensagem.
- [x] Arquivo que não é imagem é recusado pelo formulário.
- [x] "Meus feedbacks" mostra só os feedbacks do usuário, pagina de 10 em 10 e zera as notificações não lidas.
- [x] GET em excluir retorna 405.

Use `MEDIA_ROOT` temporário nos testes (`override_settings` com `tempfile.mkdtemp()`), para não deixar imagens na pasta do projeto.
