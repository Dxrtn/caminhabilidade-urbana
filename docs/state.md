# Estado atual

Atualizado em: 2026-11-24

Este arquivo guarda apenas o que não está em outro lugar. Mantenha-o com cerca de 30 linhas e retire o que estiver resolvido. O status de cada documento fica no próprio documento, e o histórico fica no Git.

## Em andamento

Nada. Specs 0001 a 0003 implementadas; 50 testes passando no PostgreSQL.

## Próximos passos

Implementar as specs em ordem, uma por vez:

1. [0004 Gestão de trechos](specs/0004-gestao-de-trechos.md)
2. [0005 Mapa e detalhes](specs/0005-mapa-e-detalhes.md)
3. [0006 Feedbacks](specs/0006-feedbacks.md)
4. [0007 Análise de feedbacks](specs/0007-analise-de-feedbacks.md)
5. [0008 Banco: permissões e exportação](specs/0008-banco-permissoes-e-exportacao.md)

## Pendências

- Prazo de entrega para Programação e Banco de Dados: 27/11/2026.
- Gerar o PDF da disciplina de Banco de Dados a partir de `banco/schema.sql`, `banco/02_permissoes.sql` e `docs/prompts.md` (spec 0008).
- **`MapaView` provisória** (`trechos/views/mapa.py` e `trechos/templates/trechos/mapa.html`): só mostra "Mapa em construção" e existe para o cadastro e o login redirecionarem a `trechos:mapa`. A spec 0005 a substitui, mantendo a rota e o nome.
- `templates/base.html` usa `{% url ... as var %}` para esconder itens de menu cujas rotas ainda não existem. Depois da spec 0007, dá para trocar por `{% url %}` direto, que acusa nomes de rota errados.
- Risco a registrar na spec 0002 ou no PRD (A07): não há limite de tentativas no login nem na verificação do código. São 6 dígitos com validade de 10 minutos, aceitável para o protótipo.
- Spec 0004: ao excluir algo pelo Django, um registro em uso gera `IntegrityError` (não `ProtectedError`), só no fim da transação. Os services só desativam trechos, então não deve acontecer.
