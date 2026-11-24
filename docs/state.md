# Estado atual

Atualizado em: 2026-11-24

Este arquivo guarda apenas o que não está em outro lugar. Mantenha-o com cerca de 30 linhas e retire o que estiver resolvido. O status de cada documento fica no próprio documento, e o histórico fica no Git.

## Em andamento

Nada. Specs 0001 a 0007 implementadas; 132 testes passando no PostgreSQL.

## Próximos passos

Implementar as specs em ordem, uma por vez:

1. [0008 Banco: permissões e exportação](specs/0008-banco-permissoes-e-exportacao.md)

## Pendências

- Prazo de entrega para Programação e Banco de Dados: 27/11/2026.
- Gerar o PDF da disciplina de Banco de Dados a partir de `banco/schema.sql`, `banco/02_permissoes.sql` e `docs/prompts.md` (spec 0008).
- `templates/base.html` usa `{% url ... as var %}` para esconder itens de menu cujas rotas ainda não existiam. Todas as rotas já existem: dá para trocar por `{% url %}` direto, que acusa nomes de rota errados.
- Risco a registrar na spec 0002 ou no PRD (A07): não há limite de tentativas no login nem na verificação do código. São 6 dígitos com validade de 10 minutos, aceitável para o protótipo.
- Limite diário (RF-20): um feedback excluído deixa de contar, então quem envia e exclui pode passar de 10 por dia. Aceitável no protótipo.
- Spec 0005: conferir no navegador, em 360 px, a página `/` (mapa na altura útil, busca e filtros sem rolagem horizontal) e o detalhe de um trecho. O Chrome automatizado não respondeu.
- O banco de desenvolvimento já tem os 36 trechos de exemplo, carregados com `carregar_trechos --exemplo --admin admin@exemplo.com`.
