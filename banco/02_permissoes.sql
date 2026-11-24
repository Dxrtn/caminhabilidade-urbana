-- =============================================================================
-- Sistema de Mapeamento de Caminhabilidade Urbana
-- 02_permissoes.sql — contas (papéis) e permissões do banco
--
-- Execute DEPOIS das migrações (python manage.py migrate), como superusuário
-- "postgres", CONECTADO AO BANCO "caminhabilidade":
--   pgAdmin: Query Tool aberto no banco caminhabilidade -> executar tudo (F5)
--   psql:    psql -U postgres -d caminhabilidade -f banco/02_permissoes.sql
--
-- O script pode ser executado mais de uma vez: os papéis só são criados se
-- ainda não existirem, e GRANT/REVOKE repetidos não causam erro.
--
-- TROQUE as senhas de exemplo ('troque_esta_senha') antes de executar.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. Papéis (contas)
-- -----------------------------------------------------------------------------
-- caminhabilidade_owner   dono das tabelas; roda as migrações (criado em 01_criar_banco.sql)
-- caminhabilidade_app     usado pela aplicação: lê e grava dados, mas não altera a estrutura
-- caminhabilidade_leitura somente leitura da view vw_trechos_mapa (relatórios, futuro painel da prefeitura)

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'caminhabilidade_app') THEN
        CREATE ROLE caminhabilidade_app WITH LOGIN PASSWORD 'troque_esta_senha';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'caminhabilidade_leitura') THEN
        CREATE ROLE caminhabilidade_leitura WITH LOGIN PASSWORD 'troque_esta_senha';
    END IF;
END
$$;


-- -----------------------------------------------------------------------------
-- 2. Fechar o acesso padrão
-- -----------------------------------------------------------------------------
-- Por padrão, qualquer papel (PUBLIC) pode conectar ao banco. Aqui, só quem
-- recebe CONNECT explicitamente. O dono do banco não é afetado.
REVOKE ALL ON DATABASE caminhabilidade FROM PUBLIC;

-- Ninguém além do dono cria objetos no schema public. (No PostgreSQL 15 ou
-- superior isso já é o padrão; o comando garante o mesmo em versões antigas.)
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO caminhabilidade_owner;


-- -----------------------------------------------------------------------------
-- 3. Aplicação: dados sim, estrutura não
-- -----------------------------------------------------------------------------
GRANT CONNECT ON DATABASE caminhabilidade TO caminhabilidade_app;
GRANT USAGE ON SCHEMA public TO caminhabilidade_app;   -- sem CREATE: não cria nem altera tabelas

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO caminhabilidade_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO caminhabilidade_app;

-- Tabelas e sequências criadas em migrações futuras (pelo dono) já nascem com
-- as mesmas permissões para a aplicação.
ALTER DEFAULT PRIVILEGES FOR ROLE caminhabilidade_owner IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO caminhabilidade_app;
ALTER DEFAULT PRIVILEGES FOR ROLE caminhabilidade_owner IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO caminhabilidade_app;


-- -----------------------------------------------------------------------------
-- 4. Leitura: apenas a view do mapa
-- -----------------------------------------------------------------------------
-- A view vw_trechos_mapa já traz só trechos ativos e nenhum dado pessoal. O papel
-- não enxerga as tabelas (usuario, feedback...), apenas o resultado da view.
GRANT CONNECT ON DATABASE caminhabilidade TO caminhabilidade_leitura;
GRANT USAGE ON SCHEMA public TO caminhabilidade_leitura;
GRANT SELECT ON vw_trechos_mapa TO caminhabilidade_leitura;


-- -----------------------------------------------------------------------------
-- 5. Demonstração (para a apresentação)
-- -----------------------------------------------------------------------------
-- Selecione as linhas abaixo SEM os "-- " e execute no Query Tool (ou no psql),
-- conectado como postgres ao banco caminhabilidade:
--
-- SET ROLE caminhabilidade_leitura;
-- SELECT logradouro, classificacao FROM vw_trechos_mapa LIMIT 5;   -- funciona
-- SELECT * FROM usuario;                                           -- ERRO: permissão negada
-- RESET ROLE;
--
-- SET ROLE caminhabilidade_app;
-- DROP TABLE feedback;                                             -- ERRO: precisa ser dono
-- RESET ROLE;
--
-- Conferir as permissões concedidas:
-- SELECT grantee, table_name, privilege_type
--   FROM information_schema.role_table_grants
--  WHERE grantee IN ('caminhabilidade_app', 'caminhabilidade_leitura')
--  ORDER BY grantee, table_name, privilege_type;
