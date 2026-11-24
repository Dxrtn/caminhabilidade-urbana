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
python manage.py exportar_sql   # regenera schema.sql
```

No pgAdmin, os dois arquivos `.sql` também podem ser abertos no Query Tool e executados de uma vez (F5): o `01` conectado ao banco `postgres`, e o `02` conectado ao banco `caminhabilidade`, ambos como o usuário `postgres`.

## Onde está cada critério da disciplina

Nomes conferidos no `schema.sql` gerado.

| Critério | Onde está |
|---|---|
| Tabelas (DDL) | `schema.sql`: 14 `CREATE TABLE`: `usuario` (com `usuario_groups` e `usuario_user_permissions`, do sistema de permissões do Django), `codigo_verificacao`, `bairro`, `obstaculo`, `trecho`, `trecho_obstaculo`, `foto_trecho`, `historico_trecho`, `feedback`, `feedback_obstaculo`, `foto_feedback` e `notificacao` |
| Integridade de entidade | Chave primária `id` em todas as tabelas (`<tabela>_pkey`); `UNIQUE` de negócio: `usuario.email`, `usuario.celular`, `bairro.nome`, `obstaculo.codigo`, `obstaculo.nome`, `uq_trecho_logradouro_referencias_lado`, `uq_trecho_obstaculo`, `uq_feedback_obstaculo` |
| Integridade de domínio | Tipos, tamanhos e `NOT NULL` das colunas; `CHECK` de opções e formatos: `ck_usuario_celular_formato`, `ck_usuario_nome_minimo`, `ck_usuario_locomocao_valida`, `ck_codigo_seis_digitos`, `ck_trecho_classificacao_valida`, `ck_trecho_lado_valido`, `ck_trecho_observacoes_tamanho`, `ck_feedback_tipo_valido`, `ck_feedback_status_valido`, `ck_feedback_classificacao_sugerida_valida`, `ck_feedback_motivo_rejeicao_valido`, `ck_feedback_descricao_tamanho` |
| Integridade referencial | 20 `FOREIGN KEY ... REFERENCES` (4 delas nas tabelas de permissões do Django), com `ON DELETE CASCADE` (ex.: fotos, obstáculos e histórico do trecho; obstáculos, fotos e notificações do feedback), `ON DELETE SET NULL` (autor e analista, para manter o relato quando a conta é removida) e o padrão `NO ACTION`, que impede excluir bairro, obstáculo ou trecho em uso ([ADR 0008](../docs/adr/0008-do-nothing-no-lugar-de-protect.md)) |
| Integridade definida pelo usuário | `CHECK` de regras de negócio: `ck_usuario_ativo_exige_verificacao`, `ck_codigo_expira_depois_de_criado`, `ck_trecho_coordenadas_em_maceio`, `ck_trecho_pontos_distintos`, `ck_feedback_rejeicao_exige_motivo`, `ck_feedback_motivo_outro_exige_texto`, `ck_feedback_analise_exige_data`; índice único parcial `uq_feedback_um_em_analise_por_trecho` (1 feedback em análise por usuário e trecho); e a trigger abaixo |
| Trigger | `trg_trecho_historico` (`AFTER INSERT OR UPDATE OF classificacao ON trecho`), que chama a função `fn_registrar_historico_trecho()` e grava em `historico_trecho` (migração `trechos.0003_trigger_historico_trecho`) |
| Campo indexado | `idx_feedback_status_criado` em `feedback (status, criado_em)`, usado pela fila de análise; `idx_trecho_bairro_classif` em `trecho (bairro_id, classificacao)`, usado pelos filtros (o nome é abreviado porque o Django limita nomes de índice a 30 caracteres). Os demais índices do `schema.sql` são criados automaticamente pelo Django para chaves estrangeiras e colunas `UNIQUE` de texto |
| Contas e permissões | `02_permissoes.sql`: `caminhabilidade_owner` (dono, roda as migrações), `caminhabilidade_app` (`SELECT, INSERT, UPDATE, DELETE` nas tabelas, sem `CREATE` no schema) e `caminhabilidade_leitura` (só `SELECT` em `vw_trechos_mapa`); `REVOKE` do acesso padrão de `PUBLIC` e `ALTER DEFAULT PRIVILEGES` para tabelas futuras |
| View | `vw_trechos_mapa` (migração `feedbacks.0002_view_trechos_mapa`): trechos ativos com o nome do bairro, dias sem atualização e quantidade de feedbacks em análise; lida pelo mapa por meio do model `TrechoMapa` |
