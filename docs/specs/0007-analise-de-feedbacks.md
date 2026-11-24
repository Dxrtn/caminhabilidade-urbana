# Spec 0007: Análise de feedbacks

- **Status:** Proposto
- **Requisitos:** RF-26, RF-29 e RF-32 a RF-34 do [PRD 0001](../prd/0001-caminhabilidade-urbana.md)
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-service.md), [ADR 0007](../adr/0007-regras-de-integridade-no-banco.md)
- **Depende de:** [Spec 0004](0004-gestao-de-trechos.md), [Spec 0006](0006-feedbacks.md)

Esta spec fecha o ciclo do sistema: o feedback do usuário, aceito pelo administrador, muda o trecho no mapa, gera histórico pela trigger e notifica o usuário.

## Exceções

`FeedbackJaAnalisado(FeedbackErro)` e `MotivoDeRejeicaoInvalido(FeedbackErro)`, além de `FeedbackNaoEncontrado`.

## `AnaliseService` (`feedbacks/services/analise_service.py`)

| Método | Regra |
|---|---|
| `fila(pagina=1, bairro_id=None, tipo=None) -> Page` | Feedbacks `EM_ANALISE`, do mais antigo para o mais recente (usa o índice `idx_feedback_status_criado`), 10 por página, com `select_related("trecho__bairro", "usuario")` e `prefetch_related("obstaculos", "fotos")` |
| `contar_em_analise() -> int` | Para o painel |
| `obter_para_analise(feedback_id) -> Feedback` | Qualquer status; inexistente → `FeedbackNaoEncontrado` |
| `outros_do_trecho(feedback) -> QuerySet` | Os outros feedbacks do mesmo trecho, para contexto |
| `aceitar(feedback_id, administrador, nova_classificacao=None, obstaculo_codigos=None, fotos_aprovadas_ids=()) -> Feedback` | Em `transaction.atomic()` e com `select_for_update()` no feedback: se não estiver em análise → `FeedbackJaAnalisado`. Marca `ACEITO`, `analisado_por` e `analisado_em`. Se `nova_classificacao` ou `obstaculo_codigos` forem informados, chama `TrechoService.alterar_classificacao(...)` com o administrador; o histórico é gravado pela trigger. Aprova as fotos indicadas (apenas fotos deste feedback). Notifica: "Seu feedback sobre {trecho} foi aceito. Obrigado!" |
| `rejeitar(feedback_id, administrador, motivo, texto="") -> Feedback` | Mesmo controle de status. `motivo` fora das opções, ou `OUTRO` sem texto → `MotivoDeRejeicaoInvalido`. Marca `REJEITADO` com motivo e dados da análise. Notifica: "Seu feedback sobre {trecho} não foi aceito. Motivo: {motivo}." |

## Forms

- `AceitarFeedbackForm`: `nova_classificacao` (opcional, com a opção "Manter a atual"), `obstaculos` (opcional, pré-marcado com os obstáculos do feedback) e `fotos_aprovadas` (checkboxes com miniaturas das fotos do feedback).
- `RejeitarFeedbackForm`: `motivo` (obrigatório) e `texto` (obrigatório quando o motivo é "Outro"; a validação de negócio fica no service).

## Rotas (`app_name = "feedbacks"`)

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/painel/feedbacks/` | `feedbacks:fila` | `FilaAnaliseView` | GET | Administrador |
| `/painel/feedbacks/<int:feedback_id>/` | `feedbacks:analisar` | `AnalisarFeedbackView` | GET | Administrador |
| `/painel/feedbacks/<int:feedback_id>/aceitar/` | `feedbacks:aceitar` | `AceitarFeedbackView` | POST | Administrador |
| `/painel/feedbacks/<int:feedback_id>/rejeitar/` | `feedbacks:rejeitar` | `RejeitarFeedbackView` | POST | Administrador |

Todas usam `AdministradorRequeridoMixin`.

## Comportamento

- **Fila:** filtros por bairro e tipo; cada item mostra trecho, tipo, data, o indicador "enviado à distância" e o número de fotos. Em celular, cartões empilhados.
- **Analisar:** mostra o feedback completo (descrição, obstáculos, fotos ampliáveis, classificação sugerida, "enviado à distância"), a situação atual do trecho e os outros feedbacks do trecho. Abaixo, os dois formulários: aceitar e rejeitar. Antes de aprovar fotos, o texto lembra: "Não aprove fotos em que apareçam rostos ou placas de veículos."
- **Aceitar/Rejeitar:** POST válido chama o service e volta para a fila com "Feedback aceito." ou "Feedback rejeitado." `FeedbackJaAnalisado` → mensagem de erro e volta para a fila. GET → 405.
- O link "Feedbacks em análise" passa a aparecer no painel ([spec 0004](0004-gestao-de-trechos.md)), com a contagem de `contar_em_analise()`. Como o painel é uma view de `trechos`, ela recebe a contagem chamando `AnaliseService` com import dentro do método, a mesma exceção de dependência descrita em [`docs/arquitetura.md`](../arquitetura.md).

## Testes

### Service

- [ ] `fila` traz só feedbacks em análise, do mais antigo para o mais recente.
- [ ] `aceitar` com nova classificação muda o trecho, e o histórico (pela trigger) registra o administrador.
- [ ] `aceitar` sem nova classificação não cria linha de histórico.
- [ ] `aceitar` aprova só as fotos indicadas e só deste feedback.
- [ ] `aceitar` ou `rejeitar` um feedback já analisado levanta `FeedbackJaAnalisado`.
- [ ] `rejeitar` com `OUTRO` sem texto levanta `MotivoDeRejeicaoInvalido`.
- [ ] Aceitar e rejeitar criam a notificação para o autor.
- [ ] Depois de aceito, o usuário pode enviar um novo feedback no mesmo trecho.

### Views

- [ ] Rotas da análise retornam 403 para usuário comum e redirecionam visitantes.
- [ ] O fluxo completo pelo cliente de teste: usuário envia → administrador aceita com nova classificação → `/api/trechos/` retorna a nova classificação.
