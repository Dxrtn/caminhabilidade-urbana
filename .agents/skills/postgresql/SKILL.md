---
name: postgresql
description: Como modelar dados e escrever SQL para o PostgreSQL neste projeto Django. Use ao criar ou alterar models, constraints, índices, migrações, triggers, views, permissões ou qualquer SQL, e ao gerar os arquivos da pasta banco/.
---

# PostgreSQL no projeto

O banco é PostgreSQL 16 ou superior, com Django 6.1 e `psycopg` 3. As decisões estão nas ADRs [0004](../../../docs/adr/0004-postgresql-como-banco-de-dados.md) e [0007](../../../docs/adr/0007-regras-de-integridade-no-banco.md). Quando houver conflito, `docs/arquitetura.md` prevalece sobre esta skill.

A disciplina de Banco de Dados avalia o SQL que as migrações geram. Por isso, o que importa aqui é o que **chega ao banco**, não só o que o Django valida em Python.

## Nomes

- Tabelas: `Meta.db_table` explícito, em `snake_case` no singular (`trecho`, `feedback`, `trecho_obstaculo`).
- Constraints e índices com nome explícito e prefixo: `ck_` (check), `uq_` (unique), `idx_` (índice). Ex.: `ck_trecho_classificacao_valida`.
- Triggers com `trg_` e funções com `fn_`. Views com `vw_`.
- Nomes em português, sem acentos.

## As quatro integridades

| Integridade | Como declarar no model |
|---|---|
| Entidade | Chave primária automática; `unique=True` ou `UniqueConstraint` para identificar a linha pelo negócio |
| Domínio | Tipo e tamanho do campo, `null=False` por padrão e `CheckConstraint` para faixas e opções |
| Referencial | `ForeignKey` com `on_delete` adequado (ver abaixo) |
| Definida pelo usuário | `CheckConstraint` com regras de negócio entre campos, `UniqueConstraint` com `condition` (índice único parcial) e triggers |

## Regras

- **`choices` não cria `CHECK` no banco.** Todo campo com `choices` precisa de uma `CheckConstraint` explícita, por exemplo `models.CheckConstraint(condition=Q(status__in=StatusFeedback.values), name="ck_feedback_status_valido")`.
- Use o argumento `condition=` em `CheckConstraint` (o antigo `check=` foi removido).
- Regras de tamanho de texto em `CheckConstraint` usam a função `Length`. Registre o lookup uma vez, no `ready()` do `AppConfig`: `TextField.register_lookup(Length)` e `CharField.register_lookup(Length)`, e escreva `Q(descricao__length__gte=10)`.
- Regras "se e somente se" viram duas alternativas: `Q(status="REJEITADO", motivo_rejeicao__isnull=False) | (~Q(status="REJEITADO") & Q(motivo_rejeicao__isnull=True))`.
- **`on_delete`:** o Django 6.1 grava o `ON DELETE` no banco com `models.DB_CASCADE`, `models.DB_SET_NULL` e `models.DB_SET_DEFAULT`. Use-os quando a remoção deve se propagar. `PROTECT` é feito pelo Django e deixa o banco com o padrão `NO ACTION`, que também impede a remoção. Não misture opções de banco e de Python em cadeia sem entender o efeito nos sinais (`DB_CASCADE` não dispara `pre_delete` nem `post_delete`).
- Índices em `Meta.indexes` com `models.Index(fields=[...], name="idx_...")`. Indexe as colunas usadas em filtros e ordenações frequentes, não todas.
- Trigger e view: em uma migração com `migrations.RunSQL(sql=..., reverse_sql=...)`, sempre com reversão. Gere a migração vazia com `python manage.py makemigrations <app> --empty --name <nome>` e declare a dependência da migração que cria as tabelas usadas.
- Tabelas preenchidas por trigger (como `historico_trecho`) nunca são gravadas pelo código Python.
- Views do banco são lidas por um model com `managed = False` e `db_table` igual ao nome da view.
- Contas e permissões (`CREATE ROLE`, `GRANT`) ficam em `banco/02_permissoes.sql`, executado manualmente, e não em migrações, pois são do servidor e não do banco da aplicação.
- Nunca interpole valores em SQL. Em SQL bruto, passe parâmetros (`cursor.execute(sql, [valor])`).

## Verificação

- Depois de criar ou alterar um model, rode `python manage.py makemigrations` e confira o SQL com `python manage.py sqlmigrate <app> <número>`. Procure os `CHECK`, `UNIQUE`, `REFERENCES ... ON DELETE` e índices esperados.
- Teste as constraints importantes gravando um dado inválido e esperando `IntegrityError` (dentro de `transaction.atomic()` no teste, para não quebrar a transação do caso de teste).
- Os testes rodam no próprio PostgreSQL; o usuário dono precisa de `CREATEDB`.
