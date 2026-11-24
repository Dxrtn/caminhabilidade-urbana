# Spec 0005: Mapa, busca, detalhes e leitura em voz

- **Status:** Implementado
- **Requisitos:** RF-09 a RF-17 do [PRD 0001](../prd/0001-caminhabilidade-urbana.md)
- **Decisões:** [ADR 0003](../adr/0003-site-web-responsivo.md), [ADR 0006](../adr/0006-mapa-com-leaflet-e-openstreetmap.md), [ADR 0007](../adr/0007-regras-de-integridade-no-banco.md)
- **Depende de:** [Spec 0003](0003-modelo-de-dados.md), [Spec 0004](0004-gestao-de-trechos.md)

> **Observação:** desde a [spec 0002](0002-contas.md) existe uma `MapaView` provisória em `trechos/views/mapa.py`, na rota `trechos:mapa`, que só renderiza `trechos/mapa.html` com o texto "Mapa em construção". Ela foi criada para o cadastro e o login terem para onde redirecionar. Esta spec **substitui** essa view e esse template pelo mapa descrito abaixo, mantendo a rota e o nome.

Para testar no navegador, carregue antes os trechos de exemplo com `python manage.py carregar_trechos --exemplo --admin <e-mail>`.

## Exceções

`TextoDeBuscaCurto(TrechoErro)`, além de `TrechoNaoEncontrado` da [spec 0004](0004-gestao-de-trechos.md).

## Objeto de saída (`trechos/services/dados.py`)

```python
@dataclass(frozen=True)
class DetalheTrecho:
    trecho: Trecho
    obstaculos: list[Obstaculo]
    fotos: list[FotoPublica]        # FotoPublica(url, descricao)
    relatos: list[Relato]           # Relato(tipo_rotulo, descricao, data, em_analise, fotos)
    desatualizado: bool
```

## `TrechoConsultaService` (`trechos/services/consulta_service.py`)

Somente leitura. Consulta o mapa pela view `vw_trechos_mapa` (model `TrechoMapa`).

| Método | Regra |
|---|---|
| `listar_para_mapa(classificacao=None, obstaculo_codigo=None) -> list[dict]` | Lê `TrechoMapa`. `classificacao` inválida é ignorada. `obstaculo_codigo` filtra pelos ids de trechos que têm o obstáculo. Cada item: `id`, `logradouro`, `bairro`, `classificacao`, `classificacao_rotulo`, `coordenadas` (`[[lat_inicio, lng_inicio], [lat_fim, lng_fim]]`, como `float`) e `feedbacks_em_analise` |
| `buscar(texto) -> list[dict]` | `texto` com menos de 3 caracteres (sem contar espaços) → `TextoDeBuscaCurto`. Busca `logradouro` ou `bairro` com `icontains` em `TrechoMapa`; no máximo 5 resultados, ordenados por logradouro. Cada item: `id`, `logradouro`, `bairro`, `referencias` e `centro` (ponto médio do trecho) |
| `obter_detalhe(trecho_id) -> DetalheTrecho` | Trecho inexistente ou inativo → `TrechoNaoEncontrado`. Fotos públicas: todas as `FotoTrecho` mais as `FotoFeedback` aprovadas de feedbacks aceitos. Relatos: os 5 feedbacks mais recentes do trecho, sem o autor e sem os rejeitados (que podem ter sido recusados por conteúdo impróprio); relato em análise vai sem fotos, e relato aceito leva só as fotos aprovadas. `desatualizado`: última atualização há mais de 180 dias |

## Rotas (`app_name = "trechos"`)

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/` | `trechos:mapa` | `MapaView` | GET | Público |
| `/api/trechos/` | `trechos:api_trechos` | `TrechosApiView` | GET | Público |
| `/api/busca/` | `trechos:api_busca` | `BuscaApiView` | GET | Público |
| `/trechos/<int:trecho_id>/` | `trechos:detalhe` | `TrechoDetalheView` | GET | Público |

## Comportamento

### `MapaView` (`trechos/mapa.html`)

Renderiza a página. A lista de obstáculos para o filtro vem de um service (ex.: `TrechoConsultaService.listar_obstaculos()`), nunca do ORM na view.

### `TrechosApiView`

`GET /api/trechos/?classificacao=PARCIAL&obstaculo=degrau` → `JsonResponse({"trechos": [...]})`.

### `BuscaApiView`

`GET /api/busca/?q=texto` → `{"resultados": [...]}`. Com `TextoDeBuscaCurto`, responde 200 com `{"resultados": [], "aviso": "Digite ao menos 3 letras."}`.

### `TrechoDetalheView` (`trechos/detalhe.html`)

Chama `obter_detalhe`; `TrechoNaoEncontrado` → 404. Mostra os dados do RF-14, os relatos do RF-15 e o aviso do RF-16 em destaque. Botões:

- **"Ouvir"** (RF-17): lê o texto montado no template em um atributo `data-texto-voz`, no formato: "Rua X, entre A e B, lado par. Classificação: parcialmente acessível. Obstáculos: degrau e poste. Atualizado em 10 de outubro de 2026." Usa `speechSynthesis` com `lang = "pt-BR"`, com botão para parar. Se o navegador não suportar, o botão não aparece.
- **"Enviar feedback"**: leva ao formulário da [spec 0006](0006-feedbacks.md). Visitante é levado ao login com `next`. Até a spec 0006 existir, o botão não aparece.
- **"Voltar ao mapa"**: abre o mapa centralizado no trecho (`/?trecho=<id>`).

## Front-end do mapa (`static/js/mapa.js`)

- Leaflet 1.9.4 por CDN (`unpkg.com/leaflet@1.9.4/dist/`), CSS no bloco `extra_head` e JS no bloco `extra_js`, só nesta página e no formulário de trecho.
- Mapa base: `https://tile.openstreetmap.org/{z}/{x}/{y}.png` com a atribuição "© OpenStreetMap contributors".
- O mapa ocupa a altura útil da tela em celular (`height: calc(100dvh - <altura do cabeçalho>)`).
- Centro: localização do usuário se ele permitir (`navigator.geolocation`, com mensagem discreta se negar); caso contrário, `[-9.6658, -35.7350]`, zoom 15. Com `?trecho=<id>`, centraliza nesse trecho e abre o popup.
- Cada trecho é uma `L.polyline` com peso 7 (fácil de tocar) e estilo por classificação, usando cor **e** padrão de linha (RF-10):

| Classificação | Cor | `dashArray` |
|---|---|---|
| Acessível | `#1b7f3b` | contínua |
| Parcialmente acessível | `#9a6700` | `"12 8"` |
| Inacessível | `#c62828` | `"2 8"` |
| Sem avaliação | `#6b6b6b` | `"20 6 2 6"` |

- Popup: logradouro, bairro, classificação em texto e o link "Ver detalhes".
- Legenda fixa no mapa com amostra de cor e padrão e o nome de cada classificação.
- Filtros (classificação e obstáculo) em `<select>` com rótulo, acima do mapa, que recarregam os trechos pela API.
- Busca: campo com rótulo, consulta `/api/busca/` com espera de 300 ms após a digitação, mostra até 5 resultados em lista acessível por teclado; ao escolher, centraliza no `centro` do trecho e abre o popup.
- Botão "Minha localização".

## Testes

### Service

- [x] `listar_para_mapa` retorna só trechos ativos, com coordenadas como lista de pares `float`.
- [x] `listar_para_mapa` filtra por classificação e por obstáculo.
- [x] `buscar` com 2 letras levanta `TextoDeBuscaCurto`; com 3 encontra por logradouro e por bairro e limita a 5.
- [x] `obter_detalhe` de trecho inativo levanta `TrechoNaoEncontrado`.
- [x] `obter_detalhe` não expõe o autor dos relatos, omite fotos de relatos em análise e mostra só fotos aprovadas.
- [x] `obter_detalhe` marca `desatualizado` com mais de 180 dias.

### Views

- [x] `/` retorna 200 para visitante e inclui o Leaflet.
- [x] `/api/trechos/` retorna JSON com os trechos e aplica os filtros.
- [x] `/api/busca/?q=ab` retorna lista vazia com aviso.
- [x] O detalhe de trecho ativo retorna 200 com o texto para voz; o de trecho inativo retorna 404.
- [x] Texto de relato com `<script>` aparece escapado no detalhe.
