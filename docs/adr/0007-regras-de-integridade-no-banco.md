# ADR 0007: Regras de integridade, histórico e view no banco de dados

- **Status:** Aceito
- **Data:** 2026-11-24

## Contexto

O Django valida dados em Python, mas, por padrão, não cria no banco as restrições de `choices`, não grava `ON DELETE` nas chaves estrangeiras e não cria triggers nem views. A disciplina de Banco de Dados avalia exatamente essas estruturas, e um dado inconsistente gravado por fora da aplicação comprometeria o mapa.

## Decisão

- Toda regra de consistência que o banco consegue expressar é declarada nos models como constraint (`CheckConstraint`, `UniqueConstraint`, inclusive parcial) e, portanto, criada no banco pelas migrações. Isso cobre as quatro integridades: de entidade, de domínio, referencial e definida pelo usuário.
- Chaves estrangeiras usam as opções de banco do Django 6.1 (`DB_CASCADE`, `DB_SET_NULL`) quando a remoção deve se propagar. Nos demais casos, usam `PROTECT`, e o banco mantém o comportamento padrão `NO ACTION`, que impede a remoção.
- O histórico de classificação dos trechos é gravado pela trigger `trg_trecho_historico`, e não pelo código Python.
- O mapa lê a view `vw_trechos_mapa`.
- Trigger e view são criadas por migrações com `RunSQL`, com SQL de reversão. Contas e permissões ficam em `banco/02_permissoes.sql`, executado manualmente.
- As tabelas têm nomes explícitos (`Meta.db_table`).

## Consequências

- O banco rejeita dados inconsistentes mesmo quando gravados por fora da aplicação.
- O SQL exportado com `sqlmigrate` mostra todas as estruturas avaliadas.
- Algumas regras ficam duplicadas: o service valida antes para mostrar uma mensagem amigável, e o banco garante.
- A trigger e a view são escritas em SQL próprio do PostgreSQL, o que prende o projeto a esse banco ([ADR 0004](0004-postgresql-como-banco-de-dados.md)).
