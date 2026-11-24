# Spec 0008: Banco — contas, permissões e exportação do SQL

- **Status:** Implementado
- **Requisitos:** RNF-05 do [PRD 0001](../prd/0001-caminhabilidade-urbana.md)
- **Decisões:** [ADR 0004](../adr/0004-postgresql-como-banco-de-dados.md), [ADR 0007](../adr/0007-regras-de-integridade-no-banco.md)
- **Depende de:** [Spec 0003](0003-modelo-de-dados.md) e de todas as migrações já criadas

Esta spec produz os arquivos entregues à disciplina de Banco de Dados, que avalia apenas o SQL das estruturas.

## Arquivos em `banco/`

| Arquivo | Conteúdo | Quem cria |
|---|---|---|
| `01_criar_banco.sql` | Dono e banco | Já existe (executado antes da spec 0001) |
| `02_permissoes.sql` | Contas e permissões | Esta spec |
| `schema.sql` | SQL de todas as migrações, gerado | Comando desta spec |
| `README.md` | O que é cada arquivo e onde está cada critério da disciplina | Já existe; esta spec completa a tabela de critérios |

## `banco/02_permissoes.sql`

Executado pelo superusuário `postgres` **depois** das migrações, conectado ao banco `caminhabilidade`, de uma vez (F5 no Query Tool do pgAdmin ou `psql -f`), sem comandos exclusivos do `psql` como `\c`. Deve ser idempotente quando possível (`DO $$ ... IF NOT EXISTS ... $$` para os papéis) e comentado em português.

| Papel | Tipo | Permissões |
|---|---|---|
| `caminhabilidade_owner` | Dono (já existe) | Dono das tabelas; roda as migrações |
| `caminhabilidade_app` | `LOGIN` | `CONNECT` no banco, `USAGE` no schema `public`, `SELECT, INSERT, UPDATE, DELETE` em todas as tabelas, `USAGE, SELECT` nas sequências. **Sem** `CREATE` no schema: a aplicação não altera a estrutura |
| `caminhabilidade_leitura` | `LOGIN` | `CONNECT`, `USAGE` no schema e **apenas** `SELECT` na view `vw_trechos_mapa`. Pensado para o futuro painel da prefeitura e para relatórios |

Também:

- `REVOKE CREATE ON SCHEMA public FROM PUBLIC;` e `REVOKE ALL ON DATABASE caminhabilidade FROM PUBLIC;`
- `ALTER DEFAULT PRIVILEGES FOR ROLE caminhabilidade_owner IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO caminhabilidade_app;` e o equivalente para sequências, para que tabelas criadas em migrações futuras já tenham as permissões.
- Ao final, um bloco comentado de **demonstração** para executar no `psql`:

```sql
-- SET ROLE caminhabilidade_leitura;
-- SELECT logradouro, classificacao FROM vw_trechos_mapa LIMIT 5;   -- funciona
-- SELECT * FROM usuario;                                           -- ERRO: permissão negada
-- RESET ROLE;
-- SET ROLE caminhabilidade_app;
-- DROP TABLE feedback;                                             -- ERRO: precisa ser dono
-- RESET ROLE;
```

As senhas no arquivo são valores de exemplo (`'troque_esta_senha'`), com comentário pedindo para trocá-las.

## Comando `exportar_sql` (`comum/management/commands/exportar_sql.py`)

```bash
python manage.py exportar_sql
```

- Percorre, em ordem, as migrações das apps `contas`, `trechos` e `feedbacks` (use o `MigrationLoader` para listar os nomes) e chama `sqlmigrate` para cada uma com `call_command`, capturando a saída.
- Grava `banco/schema.sql` com um cabeçalho (projeto, data de geração, comando usado) e, antes de cada migração, um comentário `-- Migração: <app>.<nome>`.
- Ao final, exibe quantos `CREATE TABLE`, `CHECK`, `CREATE INDEX`, `CREATE TRIGGER` e `CREATE VIEW` o arquivo contém, para conferência rápida.
- A opção `--saida <arquivo>` grava em outro caminho (usada pelo teste, para não sobrescrever o `schema.sql` versionado).

## `banco/README.md` — tabela de critérios

Complete a tabela do README com o nome real de cada objeto no banco:

| Critério da disciplina | Onde está |
|---|---|
| Tabelas com as 4 integridades | `schema.sql`: chaves primárias e `UNIQUE` (entidade); tipos, `NOT NULL` e `CHECK` de opções (domínio); `REFERENCES` com `ON DELETE` (referencial); `CHECK` e índice único parcial de regras de negócio (definida pelo usuário) |
| Trigger | `trg_trecho_historico` e a função `fn_registrar_historico_trecho` |
| Campo indexado | `idx_feedback_status_criado` e `idx_trecho_bairro_classif` |
| Contas e permissões | `02_permissoes.sql` |
| View | `vw_trechos_mapa` |

## Testes e verificação

- [x] Teste automatizado: `exportar_sql` gera um arquivo que contém `CREATE TRIGGER`, `CREATE VIEW`, `CREATE INDEX "idx_feedback_status_criado"` e `CHECK`.
- [ ] Verificação manual (registrar o resultado em `docs/state.md`): `02_permissoes.sql` executa sem erro, e a demonstração no `psql` mostra o `SELECT` permitido e as duas permissões negadas.
- [ ] Verificação manual: com `DB_USER=caminhabilidade_app` (e a senha dele) no `.env`, o sistema funciona normalmente em `python manage.py runserver`, mas, em `python manage.py dbshell`, o comando `CREATE TABLE teste (id int);` falha por falta de permissão. Depois, voltar o `.env` para o dono.
