# Estado atual

Atualizado em: 2026-11-24

Este arquivo guarda apenas o que não está em outro lugar. Mantenha-o com cerca de 30 linhas e retire o que estiver resolvido. O status de cada documento fica no próprio documento, e o histórico fica no Git.

## Em andamento

Specs 0001 a 0008 implementadas; 133 testes passando no PostgreSQL. A spec 0008 depende das verificações manuais abaixo.

## Próximos passos

1. Verificações manuais da [spec 0008](specs/0008-banco-permissoes-e-exportacao.md), com o resultado registrado aqui:
   - executar `banco/02_permissoes.sql` no pgAdmin (Query Tool no banco `caminhabilidade`, como `postgres`, com as senhas trocadas) e rodar a demonstração do fim do arquivo: `SELECT` na view funciona, `SELECT * FROM usuario` e `DROP TABLE feedback` falham;
   - trocar `DB_USER`/`DB_PASSWORD` do `.env` para `caminhabilidade_app`, conferir que o site funciona e que `CREATE TABLE teste (id int);` falha no `python manage.py dbshell`; depois voltar o `.env` para o dono.
2. Gerar o PDF da disciplina de Banco de Dados a partir de `banco/schema.sql`, `banco/02_permissoes.sql` e `docs/prompts.md`.

## Pendências

- Prazo de entrega para Programação e Banco de Dados: 27/11/2026.
- `templates/base.html` usa `{% url ... as var %}` para esconder itens de menu cujas rotas ainda não existiam. Todas as rotas já existem: dá para trocar por `{% url %}` direto, que acusa nomes de rota errados.
- Risco a registrar na spec 0002 ou no PRD (A07): não há limite de tentativas no login nem na verificação do código. São 6 dígitos com validade de 10 minutos, aceitável para o protótipo.
- Limite diário (RF-20): um feedback excluído deixa de contar, então quem envia e exclui pode passar de 10 por dia. Aceitável no protótipo.
- Spec 0005: conferir no navegador, em 360 px, a página `/` (mapa na altura útil, busca e filtros sem rolagem horizontal) e o detalhe de um trecho. O Chrome automatizado não respondeu.
- O banco de desenvolvimento já tem os 36 trechos de exemplo, carregados com `carregar_trechos --exemplo --admin admin@exemplo.com`.
