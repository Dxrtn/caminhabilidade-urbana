-- =============================================================================
-- Sistema de Mapeamento de Caminhabilidade Urbana
-- 01_criar_banco.sql — cria o usuário dono e o banco de dados
--
-- Execute UMA VEZ, como superusuário do PostgreSQL, ANTES da primeira migração:
--   psql -U postgres -f banco/01_criar_banco.sql
-- (no Windows, também pode ser executado pelo Query Tool do pgAdmin,
--  conectado ao banco "postgres")
--
-- TROQUE a senha abaixo e use a mesma no arquivo .env (DB_PASSWORD).
-- =============================================================================

-- Dono das tabelas: é com este usuário que o Django roda as migrações.
-- CREATEDB é necessário para o Django criar o banco temporário dos testes.
CREATE ROLE caminhabilidade_owner
    WITH LOGIN
    PASSWORD 'phdd123'
    CREATEDB;

-- Banco do sistema, em UTF-8, pertencente ao dono.
CREATE DATABASE caminhabilidade
    WITH OWNER = caminhabilidade_owner
    ENCODING = 'UTF8'
    TEMPLATE = template0;

-- As contas da aplicação e de leitura, com permissões restritas,
-- são criadas depois das migrações, em 02_permissoes.sql (spec 0008).
