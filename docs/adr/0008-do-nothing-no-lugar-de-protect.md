# ADR 0008: `DO_NOTHING` no lugar de `PROTECT` nas chaves estrangeiras

- **Status:** Aceito
- **Data:** 2026-11-24

## Contexto

A [ADR 0007](0007-regras-de-integridade-no-banco.md) usa as opções de banco do Django 6.1 (`DB_CASCADE`, `DB_SET_NULL`) quando a remoção deve se propagar, e `PROTECT` nos demais casos.

O Django 6.1 não aceita essa combinação. Um model não pode ter chaves estrangeiras com `on_delete` de banco e de Python ao mesmo tempo (check `models.E050`), e a cadeia de referências entre models precisa usar um único tipo (check `fields.E323`). `Trecho` tem `atualizado_por` com `DB_SET_NULL` e `bairro` com `PROTECT`; `Feedback` tem `usuario` com `DB_SET_NULL` e `trecho` com `PROTECT`. Com isso, `python manage.py check` falha.

`DO_NOTHING` é a única opção que os dois checks ignoram. Ela não executa nada em Python e deixa no banco o padrão `NO ACTION`, o mesmo que `PROTECT` deixava.

As alternativas eram trocar `DB_CASCADE` e `DB_SET_NULL` por `CASCADE` e `SET_NULL`, feitos pelo Django, o que tiraria o `ON DELETE` do SQL avaliado pela disciplina de Banco de Dados, ou silenciar os checks, o que esconderia erros reais.

## Decisão

As chaves estrangeiras que devem impedir a remoção usam `on_delete=models.DO_NOTHING`: `Trecho.bairro`, `TrechoObstaculo.obstaculo`, `Feedback.trecho` e `FeedbackObstaculo.obstaculo`. O banco garante o bloqueio com `NO ACTION`. As demais continuam com `DB_CASCADE` e `DB_SET_NULL`.

Esta decisão substitui apenas o trecho da ADR 0007 que recomenda `PROTECT`; o restante dela continua valendo.

## Consequências

- O SQL das migrações continua com `ON DELETE CASCADE`, `ON DELETE SET NULL` e, nas demais, o `NO ACTION` padrão, como a ADR 0007 pretendia.
- Excluir pelo Django um registro em uso não levanta `ProtectedError`. O banco recusa com `IntegrityError` e, como as chaves do Django são `DEFERRABLE INITIALLY DEFERRED`, o erro aparece só ao fim da transação. Os services não excluem trechos (a spec 0004 só desativa), e o Admin bloqueia a exclusão de `Bairro` e `Obstaculo`.
- Os testes que verificam o bloqueio usam `SET CONSTRAINTS ALL IMMEDIATE` antes do `DELETE`.
