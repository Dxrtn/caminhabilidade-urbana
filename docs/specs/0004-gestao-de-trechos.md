# Spec 0004: Gestão de trechos

- **Status:** Implementado
- **Requisitos:** RF-08 e RF-27 a RF-31 do [PRD 0001](../prd/0001-caminhabilidade-urbana.md)
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-service.md), [ADR 0006](../adr/0006-mapa-com-leaflet-e-openstreetmap.md), [ADR 0007](../adr/0007-regras-de-integridade-no-banco.md)
- **Depende de:** [Spec 0002](0002-contas.md), [Spec 0003](0003-modelo-de-dados.md)

## Exceções (`trechos/exceptions.py`)

Herdam de `TrechoErro(Exception)`: `TrechoNaoEncontrado`, `TrechoDuplicado`, `DadosDeTrechoInvalidos`.

## Objeto de dados (`trechos/services/dados.py`)

```python
@dataclass(frozen=True)
class DadosTrecho:
    logradouro: str
    bairro: str                 # nome do bairro
    referencia_inicio: str
    referencia_fim: str
    lado: str
    lat_inicio: Decimal
    lng_inicio: Decimal
    lat_fim: Decimal
    lng_fim: Decimal
    classificacao: str = Classificacao.SEM_AVALIACAO
    obstaculos: tuple[str, ...] = ()   # códigos dos obstáculos
    observacoes: str = ""
```

## `TrechoService` (`trechos/services/trecho_service.py`)

| Método | Regra |
|---|---|
| `listar_para_gestao(texto=None, bairro_id=None, classificacao=None, desatualizados=False, pagina=1) -> Page` | Todos os trechos, ativos e inativos, 10 por página, ordenados por `logradouro`. `texto` filtra logradouro (`icontains`); `desatualizados` filtra `atualizado_em` com mais de 180 dias. Usa `select_related("bairro")` |
| `obter(trecho_id) -> Trecho` | Levanta `TrechoNaoEncontrado` |
| `criar(dados: DadosTrecho, administrador, fotos=()) -> Trecho` | Em `transaction.atomic()`: resolve o bairro pelo nome (inexistente → `DadosDeTrechoInvalidos`), cria o trecho com `atualizado_por=administrador`, liga os obstáculos e grava as fotos. Trecho repetido → `TrechoDuplicado` (verificado antes e, como garantia, convertendo o `IntegrityError` da constraint) |
| `atualizar(trecho_id, dados: DadosTrecho, administrador, novas_fotos=()) -> Trecho` | Atualiza campos e obstáculos e acrescenta fotos, definindo `atualizado_por`. O histórico é gravado pela trigger quando a classificação muda |
| `alterar_classificacao(trecho_id, classificacao, administrador, obstaculo_codigos=None) -> Trecho` | Usado pela análise de feedbacks ([spec 0007](0007-analise-de-feedbacks.md)). Atualiza só classificação e, se informados, obstáculos |
| `desativar(trecho_id, administrador)` / `reativar(trecho_id, administrador)` | Altera `ativo`. Nunca exclui |
| `historico(trecho_id) -> QuerySet[HistoricoTrecho]` | Do mais recente para o mais antigo |

## Carga em lote: abstração, herança e polimorfismo (`trechos/services/importadores.py`)

Padrão *Template Method*: a classe abstrata define o algoritmo de importação, e as subclasses só dizem **de onde** vêm os dados.

```python
@dataclass
class ResultadoImportacao:
    importados: int = 0
    ignorados: int = 0                                     # já existiam
    erros: list[str] = field(default_factory=list)        # "linha 3: bairro 'X' não existe"


class ImportadorDeTrechos(ABC):
    def __init__(self, administrador):
        self._administrador = administrador

    @abstractmethod
    def ler(self) -> Iterable[DadosTrecho]:
        """Cada subclasse devolve os dados da sua origem."""

    def importar(self) -> ResultadoImportacao:
        """Algoritmo comum: para cada item, cria pelo TrechoService e contabiliza."""
```

| Subclasse | Origem |
|---|---|
| `ImportadorDadosExemplo` | Lista `TRECHOS_EXEMPLO` em `trechos/dados_exemplo.py` |
| `ImportadorCsv` | Arquivo CSV (UTF-8, separador `;`) com o cabeçalho: `logradouro;bairro;referencia_inicio;referencia_fim;lado;lat_inicio;lng_inicio;lat_fim;lng_fim;classificacao;obstaculos;observacoes`. `obstaculos` separados por `,` |

Regras de `importar()`: `TrechoDuplicado` conta como ignorado; `DadosDeTrechoInvalidos`, `IntegrityError` e valores mal formatados viram uma mensagem em `erros`, sem interromper as demais linhas. Cada linha é gravada em sua própria transação.

### Dados de exemplo (`trechos/dados_exemplo.py`)

Entre 30 e 40 trechos em **Ponta Verde, Pajuçara e Jatiúca**, em ruas reais desses bairros (ex.: Av. Álvaro Otacílio, Av. Dr. Antônio Gouveia, Rua Jangadeiros Alagoanos, Av. Sandoval Arroxelas), cada um cobrindo cerca de uma quadra (50 a 150 m), com coordenadas aproximadas mas sobre a rua. Distribuição: ~35% acessível, ~30% parcialmente acessível, ~20% inacessível e ~15% sem avaliação, com obstáculos coerentes com a classificação e observações curtas. Os dados são fictícios e servem apenas para demonstração.

### Comando `carregar_trechos`

```bash
python manage.py carregar_trechos --exemplo --admin admin@exemplo.com
python manage.py carregar_trechos --csv caminho/arquivo.csv --admin admin@exemplo.com
```

- Exatamente uma das opções `--exemplo` ou `--csv`. `--admin` é o e-mail de um usuário `is_staff`; caso contrário, o comando falha sem gravar.
- Escolhe a subclasse do importador e chama `importar()`, sem saber qual é a origem (polimorfismo).
- Exibe o resumo: importados, ignorados e cada erro.
- Pode ser executado de novo sem duplicar trechos.

## Form (`trechos/forms/trecho_form.py`)

`TrechoForm(forms.Form)` com os campos de `DadosTrecho`, sendo `bairro` um `ModelChoiceField`, `obstaculos` um `ModelMultipleChoiceField` com checkboxes, `fotos` com seleção múltipla de imagens (até 5, de até 5 MB cada) e as coordenadas como `DecimalField` com `step="0.000001"`. Validação de formato: coordenadas dentro dos limites de Maceió e início diferente do fim, com mensagens claras.

Na página do formulário, um mapa Leaflet pequeno mostra a linha entre os dois pontos e permite preencher as coordenadas clicando: primeiro clique define o início, segundo define o fim. Os campos numéricos continuam editáveis.

## Rotas (`app_name = "trechos"`)

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/painel/` | `trechos:painel` | `PainelView` | GET | Administrador |
| `/painel/trechos/` | `trechos:gestao` | `TrechoGestaoListView` | GET | Administrador |
| `/painel/trechos/novo/` | `trechos:criar` | `TrechoCreateView` | GET, POST | Administrador |
| `/painel/trechos/<int:trecho_id>/editar/` | `trechos:editar` | `TrechoUpdateView` | GET, POST | Administrador |
| `/painel/trechos/<int:trecho_id>/desativar/` | `trechos:desativar` | `TrechoDesativarView` | POST | Administrador |
| `/painel/trechos/<int:trecho_id>/reativar/` | `trechos:reativar` | `TrechoReativarView` | POST | Administrador |

Todas usam `AdministradorRequeridoMixin`. `TrechoNaoEncontrado` vira 404.

## Comportamento

- **Painel:** página inicial da administração, com links para "Trechos" e "Feedbacks em análise". A rota da análise existe a partir da [spec 0007](0007-analise-de-feedbacks.md); até lá, o link não aparece.
- **Lista:** filtros por texto, bairro, classificação e a opção "Sem atualização há mais de 6 meses". Cada linha mostra logradouro, bairro, classificação (texto + cor), status ativo/inativo e data da última atualização. Em celular, a lista vira cartões empilhados.
- **Criar/editar:** POST válido chama o service e redireciona para a lista com "Trecho salvo." `TrechoDuplicado` aparece como erro do formulário.
- **Editar:** abaixo do formulário, o histórico de classificação (data, anterior → nova, autor) lido de `TrechoService.historico`.
- **Desativar/reativar:** POST, com confirmação no navegador (`confirm`) antes do envio, e mensagem de sucesso.

Templates em `trechos/templates/trechos/painel/`.

## Testes

### Service e importadores

- [x] `criar` grava o trecho com obstáculos e `atualizado_por`, e a trigger registra o histórico inicial.
- [x] `criar` com bairro inexistente levanta `DadosDeTrechoInvalidos`; com trecho repetido, `TrechoDuplicado`.
- [x] `atualizar` mudando a classificação gera uma linha de histórico com o administrador.
- [x] `desativar` mantém o trecho no banco e o tira de `TrechoMapa`.
- [x] `listar_para_gestao` filtra por texto, bairro, classificação e desatualizados, e pagina de 10 em 10.
- [x] `ImportadorDadosExemplo` importa todos os trechos de exemplo; rodar de novo só gera ignorados.
- [x] `ImportadorCsv` importa um CSV válido e relata a linha com bairro inexistente sem parar as outras.
- [x] O comando falha sem gravar quando `--admin` não é administrador.

### Views

- [x] Rotas do painel redirecionam visitantes ao login e retornam 403 para usuário comum.
- [x] Administrador cria e edita um trecho pelo formulário.
- [x] GET em desativar e reativar retorna 405.
