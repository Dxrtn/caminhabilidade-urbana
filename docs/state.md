# Estado atual

Atualizado em: 2026-11-24

Este arquivo guarda apenas o que não está em outro lugar. Mantenha-o com cerca de 30 linhas e retire o que estiver resolvido. O status de cada documento fica no próprio documento, e o histórico fica no Git.

## Em andamento

Nada. Spec 0001 implementada; 13 testes passando no PostgreSQL.

## Próximos passos

Implementar as specs em ordem, uma por vez:

1. [0002 Contas](specs/0002-contas.md)
2. [0003 Modelo de dados](specs/0003-modelo-de-dados.md)
3. [0004 Gestão de trechos](specs/0004-gestao-de-trechos.md)
4. [0005 Mapa e detalhes](specs/0005-mapa-e-detalhes.md)
5. [0006 Feedbacks](specs/0006-feedbacks.md)
6. [0007 Análise de feedbacks](specs/0007-analise-de-feedbacks.md)
7. [0008 Banco: permissões e exportação](specs/0008-banco-permissoes-e-exportacao.md)

## Pendências

- Prazo de entrega para Programação e Banco de Dados: 27/11/2026.
- Gerar o PDF da disciplina de Banco de Dados a partir de `banco/schema.sql`, `banco/02_permissoes.sql` e `docs/prompts.md` (spec 0008).
- Spec 0001, critério "página base em 360 px sem rolagem horizontal": conferir no navegador assim que existir a primeira página (spec 0002). O HTML e o CSS já renderizam, mas não houve teste visual.
- `templates/base.html` usa `{% url ... as var %}` para esconder itens de menu cujas rotas ainda não existem. Depois da spec 0007, dá para trocar por `{% url %}` direto, que acusa nomes de rota errados.