# Registro de uso de IA

Exigido pela disciplina de Laboratório de Banco de Dados: "informar qual o modelo de IA usado e o prompt usado". Também documenta o desenvolvimento assistido por IA para a disciplina de Laboratório de Programação.

**Regra:** toda interação com IA que gere ou altere documentos ou código entra aqui, em ordem, com o texto literal do pedido. A IA acrescenta a entrada ao concluir cada tarefa (ver `AGENTS.md`). Revisões e correções feitas pela dupla também entram, para mostrar o que foi ajustado.

## Ferramentas e modelos

| Etapa | Ferramenta | Modelo |
|---|---|---|
| Planejamento e documentação inicial (PRD, ADRs, specs, skills) | Claude (claude.ai) | Claude Opus 5.5 |
| Implementação | Claude Code (extensão do VS Code) | Claude Opus 5.5 |

## Modelo de entrada

```markdown
### NNN — AAAA-MM-DD — Título curto

- **Ferramenta / modelo:**
- **Quem pediu:** Davi / Pedro
- **Spec:** 000X

**Prompt:**

> texto literal

**Resultado:** o que foi feito, em 1 a 3 linhas.

**Revisão da dupla:** o que foi conferido ou corrigido.
```

## Entradas

### 001 — 2026-11-23 — Plano do projeto integrado

- **Ferramenta / modelo:** Claude (claude.ai) / Claude Opus 5.5
- **Quem pediu:** Davi
- **Spec:** —

**Prompt** (enviado junto com o Documento de Requisitos, as instruções das disciplinas de Programação e Banco de Dados e o link do repositório-modelo do professor):

> Vou tentar te passar um contexto bem completinho para você poder entender do que se trata a missão que eu e minha dupla devemos terminar em relação ao mesmo projeto que foi abordado nesse chat (e por isso decidi continuar daqui).
>
> Eu e minha dupla estamos na reta final onde devemos desenvolver o projeto final abrangendo tudo o que vimos e a partir do que foi orientado pelos professores durante as aulas.
>
> Esse projeto vai envolver 3 matérias, e cada uma vai avaliar uma coisa diferente no mesmo projeto desenvolvido:
>
> * Engenharia de software - será avaliado nosso documento de requisitos que estamos construindo desde o começo e alimentando conforme o tempo e por agora já está completo
> * Laboratório de programação - será avaliado o código fonte e as estruturas dos arquivos que foram utilizados para o desenvolvimento assistido com IA (docs, specs, skills e etc)
> * Laboratório de banco de dados - será avaliado exclusivamente a parte da persistência de dados do projeto
>
> Anexei para você o documento de requisitos considerado final, o pdf disponibilizado pelo professor de programação com as instruções do que ele quer no projeto e a mesma coisa para o professor de banco de dados.
>
> Além disso, o professor de programação passou para nós um link de github que serve como modelo para o desenvolvimento do código. A ideia que ele passou é transformar todo o documento de requisitos em tarefas para a IA ir desenvolvendo juntamente com os arquivos de restrições, skills e etc. Analise bem do que se trata todo o repositório: https://github.com/own4rd/labiv20262/
>
> De maneira geral, é algo rápido de se fazer, mas exige revisão da dupla e entendimento do que está sendo construído também.
>
> [trecho sobre os prazos de entrega omitido]
>
> Com isso tudo, eu preciso que você instrua eu e minha dupla de como vamos proceder com o desenvolvimento do projeto a partir do que já temos pronto e preparado e também com as instruções dos professores.

**Resultado:** plano de trabalho: análise do repositório-modelo, decisões de stack (Django, site responsivo, PostgreSQL), escolha dos requisitos do protótipo, modelo de dados com as 4 integridades, trigger, índice, view e permissões, mapa dos pilares de POO e cronograma da dupla.

**Revisão da dupla:** decisões confirmadas: Django, site web responsivo para uso no celular e PostgreSQL.

### 002 — 2026-11-24 — Documentação inicial do repositório

- **Ferramenta / modelo:** Claude (claude.ai) / Claude Opus 5.5
- **Quem pediu:** Davi
- **Spec:** todas (0001 a 0008)

**Prompt:**

> Gostei de todo o direcionamento, agora eu preciso sair daqui do claude chat e ir desenvolver isso. Preciso que me ajude com isso. Depois que você gerar todos os arquivos necessários para começar no vscode, vou criar um projeto novo e instalar o django para poder implementar a partir dos documentos.
>
> Vai ser em django para aproveitar o conteúdo do repositório;
> vai ser um site web responsivo (importante) para uso mobile;
> banco em postgres com certeza.
>
> AVISO IMPORTANTE: quero deixar claro que o que vamos desenvolver é um protótipo minimamente funcional, não se tratando do sistema completo. Vamos desenvolver apenas para ter algo concreto e conseguir apresentar mostrando aos professores que o sistema (protótipo) tem suas funcionalidades reais.

**Resultado:** `AGENTS.md`, PRD 0001, `arquitetura.md`, 7 ADRs, 8 specs, `poo.md`, skill `postgresql`, `banco/01_criar_banco.sql` e README com o roteiro de implementação. As skills do repositório-modelo foram mantidas.

**Revisão da dupla:** *(preencher depois de ler o PRD e as specs)*

### 003 — 2026-11-24 — Implementação da spec 0001 (fundação)

- **Ferramenta / modelo:** Claude Code (extensão do VS Code) / Claude Opus 5.5
- **Quem pediu:** Davi
- **Spec:** 0001

**Prompt:**

> Leia o AGENTS.md e implemente a spec docs/specs/0001-fundacao.md, seguindo docs/arquitetura.md e as skills indicadas.
> Implemente apenas esta spec. Escreva os testes listados nela e rode python manage.py test até passar.
> Ao final, marque os testes cumpridos e o status da spec, atualize docs/state.md, docs/poo.md e docs/prompts.md,
> e me mostre um resumo do que foi criado, arquivo por arquivo, explicando as decisões principais.

**Resultado:** projeto `core` e apps `comum`, `contas`, `trechos` e `feedbacks` em pacotes; `settings.py` lendo o `.env`; `ModeloComDatas`, `AdministradorRequeridoMixin`, `distancia_em_metros`; model `contas.Usuario` com as quatro `CHECK` no banco (migração `contas/0001_initial`) e Admin ajustado; `templates/base.html` e `static/css/site.css` pensados primeiro para celular; 13 testes, incluindo o teste de arquitetura, passando no PostgreSQL. Ajustes além do texto da spec: `is_active` com padrão falso, remoção de `first_name`/`last_name` e validadores nos campos `celular` e `nome_completo` (para o `createsuperuser` recusar dados inválidos com mensagem).

**Revisão da dupla:** *(preencher)*

### 004 — 2026-11-24 — Caminho das skills

- **Ferramenta / modelo:** Claude Code (extensão do VS Code) / Claude Opus 5.5
- **Quem pediu:** Davi
- **Spec:** —

**Prompt:**

> corrija os caminhos para as skills estarem dentro dos agents

**Resultado:** pasta `skills/` movida para `.agents/skills/` (com `git mv`), o caminho que o `AGENTS.md` e as specs já usavam. Removido da skill `seguranca-owasp` um link para uma ADR do repositório-modelo que não existe neste projeto.

**Revisão da dupla:** *(preencher)*

### 005 — 2026-11-24 — Implementação da spec 0002 (contas)

- **Ferramenta / modelo:** Claude Code (extensão do VS Code) / Claude Opus 5.5
- **Quem pediu:** Davi
- **Spec:** 0002

**Prompt:**

> Leia o AGENTS.md e implemente a spec docs/specs/0002-contas.md, seguindo docs/arquitetura.md e as skills indicadas.
> Implemente apenas esta spec. Escreva os testes listados nela e rode python manage.py test até passar.
>
> Ajuste necessário: a spec 0002 redireciona para "trechos:mapa", mas o mapa só será implementado na spec 0005.
> Crie agora em trechos/urls.py (app_name = "trechos") a rota "" com nome "mapa", apontando para uma MapaView
> provisória (herdando de View) que renderiza trechos/mapa.html com o texto "Mapa em construção" usando o base.html.
> Registre essa pendência em docs/state.md e acrescente na spec 0005 uma observação de que ela substitui essa view provisória.
>
> Ao final, marque os testes cumpridos e o status da spec, atualize docs/state.md, docs/poo.md e docs/prompts.md,
> e me mostre um resumo do que foi criado, arquivo por arquivo, explicando as decisões principais.

**Resultado:** model `CodigoVerificacao` com `ck_codigo_seis_digitos`, `ck_codigo_expira_depois_de_criado` e `ON DELETE CASCADE` (migração `contas/0002`); `EnviadorDeCodigo` e suas duas subclasses; exceções de `contas`; `CadastroService` e `VerificacaoService`; `CadastroForm`, `VerificacaoForm` e `EntrarForm`; as cinco views e rotas de contas, com templates; `MapaView` provisória; 21 testes novos (34 no total) passando. Além do texto da spec: o e-mail é guardado e comparado em minúsculas, e foi criado `VerificacaoService.obter_pendente()` para a view mostrar o celular mascarado sem acessar o ORM.

**Revisão da dupla:** *(preencher)*

### 006 — 2026-11-24 — Conferência dos 360 px e commit da spec 0002

- **Ferramenta / modelo:** Claude Code (extensão do VS Code) / Claude Opus 5.5
- **Quem pediu:** Davi
- **Spec:** 0001 e 0002

**Prompt:**

> verifiquei os 360px e está ok
> implemente a segurança
> faça o commit dessa segunda spec

**Resultado:** critério de 360 px da spec 0001 marcado com base na conferência manual da dupla, e spec 0002 commitada. O limite de tentativas não foi implementado: o PRD o lista em "Fora do escopo" ("bloqueio por tentativas"), e a decisão sobre ele ficou com a dupla.

**Revisão da dupla:** 360 px conferidos no navegador por Davi.

### 007 — 2026-11-24 — Implementação da spec 0003 (modelo de dados)

- **Ferramenta / modelo:** Claude Code (extensão do VS Code) / Claude Opus 5.5
- **Quem pediu:** Davi
- **Spec:** 0003

**Prompt:**

> Leia o AGENTS.md e implemente a spec docs/specs/0003-modelo-de-dados.md, seguindo docs/arquitetura.md
> e as skills indicadas, principalmente .agents/skills/postgresql/SKILL.md.
> Implemente apenas esta spec. Escreva os testes listados nela e rode python manage.py test até passar.
>
> Atenção à ordem das migrações:
> - a trigger (RunSQL em trechos) depende das tabelas trecho e historico_trecho;
> - a view (RunSQL em feedbacks) depende das tabelas trecho, bairro e feedback;
> - declare essas dependências explicitamente em cada migração.
> Os nomes das colunas do model HistoricoTrecho precisam bater exatamente com o INSERT da trigger.
>
> Ao final:
> 1. Rode python manage.py sqlmigrate para cada migração nova e me mostre uma tabela listando cada
>    constraint, índice, trigger e view criados, com o nome real no banco e qual das 4 integridades
>    (entidade, domínio, referencial, definida pelo usuário) cada constraint representa.
> 2. Marque os testes cumpridos e o status da spec, atualize docs/state.md, docs/poo.md e docs/prompts.md.
> 3. Me mostre um resumo do que foi criado, arquivo por arquivo, explicando as decisões principais.

**Resultado:** models de `trechos` (`Bairro`, `Obstaculo`, `Trecho`, `TrechoObstaculo`, `FotoTrecho`, `HistoricoTrecho`, `TrechoMapa`) e de `feedbacks` (`Feedback`, `FeedbackObstaculo`, `FotoFeedback`, `Notificacao`) com todas as constraints e índices da spec; migração de dados com 12 obstáculos e 49 bairros; trigger `trg_trecho_historico` e view `vw_trechos_mapa` em `RunSQL` com reversão e dependências explícitas; Admin somente leitura; 16 testes novos (50 no total). Desvios forçados pelo Django 6.1, documentados na spec e na ADR 0008 (proposta): `DO_NOTHING` no lugar de `PROTECT` (checks E050/E323) e índice `idx_trecho_bairro_classif` (limite de 30 caracteres, E034). Acrescentada `ck_feedback_motivo_rejeicao_valido`, exigida pela skill postgresql. Skills postgresql e django-boas-praticas atualizadas com essas regras.

**Revisão da dupla:** ADR 0008 aceita por Davi.
