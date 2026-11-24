# ADR 0004: PostgreSQL como banco de dados

- **Status:** Aceito
- **Data:** 2026-11-24

## Contexto

O projeto-modelo da disciplina usa SQLite. A disciplina de Banco de Dados avalia, além das tabelas, a criação de contas de acesso com permissões, trigger, índice e view. O SQLite não tem contas nem permissões (`CREATE ROLE` e `GRANT` não existem) e tem suporte limitado a constraints complexas.

## Decisão

O projeto usa PostgreSQL (versão 16 ou superior), acessado pelo driver `psycopg` 3. As credenciais vêm de variáveis de ambiente (arquivo `.env`). O banco e o usuário dono são criados por `banco/01_criar_banco.sql`.

## Consequências

- O banco atende a todos os critérios da disciplina de Banco de Dados, incluindo contas e permissões.
- Constraints parciais e funções PL/pgSQL ficam disponíveis.
- Cada integrante precisa instalar e configurar o PostgreSQL localmente.
- Os testes automatizados também rodam no PostgreSQL, e o usuário dono precisa da permissão `CREATEDB` para o Django criar o banco de testes.
