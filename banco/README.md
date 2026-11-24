# Banco de dados

SQL do sistema, entregue à disciplina de Laboratório de Banco de Dados. O banco é PostgreSQL ([ADR 0004](../docs/adr/0004-postgresql-como-banco-de-dados.md)), e as estruturas são criadas pelas migrações do Django, com constraints, trigger e view declaradas conforme a [ADR 0007](../docs/adr/0007-regras-de-integridade-no-banco.md).

## Arquivos

| Arquivo | O que é | Quando executar |
|---|---|---|
| `01_criar_banco.sql` | Cria o usuário dono e o banco | Uma vez, antes da primeira migração |
| `schema.sql` | SQL de todas as migrações, gerado por `python manage.py exportar_sql` | Não é executado: é a documentação exata do que as migrações criam |
| `02_permissoes.sql` | Contas da aplicação e de leitura, com permissões | Depois das migrações |

## Ordem para montar o banco do zero

```bash
psql -U postgres -f banco/01_criar_banco.sql
python manage.py migrate
psql -U postgres -d caminhabilidade -f banco/02_permissoes.sql
```

## Onde está cada critério da disciplina

A tabela abaixo é completada na [spec 0008](../docs/specs/0008-banco-permissoes-e-exportacao.md), com os nomes reais dos objetos.

| Critério | Onde está |
|---|---|
| Tabelas (DDL) com as 4 integridades | |
| Trigger | |
| Campo indexado | |
| Contas e permissões | |
| View | |
