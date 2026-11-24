# Estado atual

Atualizado em: 2026-11-24

Este arquivo guarda apenas o que não está em outro lugar. Mantenha-o com cerca de 30 linhas e retire o que estiver resolvido. O status de cada documento fica no próprio documento, e o histórico fica no Git.

## Em andamento

Nada. Specs 0001 a 0005 implementadas; 88 testes passando no PostgreSQL.

## Próximos passos

Implementar as specs em ordem, uma por vez:

1. [0006 Feedbacks](specs/0006-feedbacks.md)
2. [0007 Análise de feedbacks](specs/0007-analise-de-feedbacks.md)
3. [0008 Banco: permissões e exportação](specs/0008-banco-permissoes-e-exportacao.md)

## Pendências

- Prazo de entrega para Programação e Banco de Dados: 27/11/2026.
- Gerar o PDF da disciplina de Banco de Dados a partir de `banco/schema.sql`, `banco/02_permissoes.sql` e `docs/prompts.md` (spec 0008).
- `templates/base.html` usa `{% url ... as var %}` para esconder itens de menu cujas rotas ainda não existem. Depois da spec 0007, dá para trocar por `{% url %}` direto, que acusa nomes de rota errados.
- Risco a registrar na spec 0002 ou no PRD (A07): não há limite de tentativas no login nem na verificação do código. São 6 dígitos com validade de 10 minutos, aceitável para o protótipo.
- Spec 0006: ligar o botão "Enviar feedback" em `trechos/templates/trechos/detalhe.html` (há um comentário marcando o lugar); visitante vai ao login com `next`.
- Spec 0005: conferir no navegador, em 360 px, a página `/` (mapa na altura útil, busca e filtros sem rolagem horizontal) e o detalhe de um trecho. O Chrome automatizado não respondeu.
- O banco de desenvolvimento já tem os 36 trechos de exemplo, carregados com `carregar_trechos --exemplo --admin admin@exemplo.com`.
