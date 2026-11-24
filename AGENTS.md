# Regras essenciais

- Este projeto é um **protótipo** acadêmico. Implemente apenas o que está no PRD e nas specs. O que estiver em "Fora do escopo" não deve ser construído, nem parcialmente.
- O projeto segue MVT, e toda regra de negócio e consulta ao ORM fica nos services.
- Toda view é uma classe que herda de `django.views.View` e implementa só os métodos HTTP necessários. Mixins de acesso, como `LoginRequiredMixin`, são permitidos.
- Services não recebem `request` nem retornam `HttpResponse`.
- A interface é um site responsivo, pensado primeiro para telas de celular (a partir de 360 px de largura).
- O banco é PostgreSQL. Constraints, índices, trigger e view fazem parte da avaliação: não os remova nem os substitua por validação apenas em Python.

# Ao iniciar e concluir

- Ao iniciar, leia `docs/state.md`, com o trabalho em andamento, os próximos passos e as pendências.
- Ao concluir uma tarefa:
  1. Atualize `docs/state.md` e retire o que estiver resolvido.
  2. Se criou ou alterou uma classe citada em `docs/poo.md`, atualize o caminho e a explicação nesse arquivo.
  3. Acrescente uma entrada em `docs/prompts.md` com o pedido recebido (texto literal), a ferramenta e o modelo de IA, e um resumo do que foi feito. Esse registro é exigido pela disciplina de Banco de Dados.

# Antes de alterar código

- Leia `docs/arquitetura.md`, com as regras completas de cada camada.
- Leia a especificação da funcionalidade em `docs/specs/`, seguindo a ordem da numeração. Implemente uma spec por vez.
- Em código Python, leia `.agents/skills/python-boas-praticas/SKILL.md`.
- Em código Django, leia também `.agents/skills/django-boas-praticas/SKILL.md`.
- Em models, migrações, constraints, índices, triggers, views ou SQL, leia `.agents/skills/postgresql/SKILL.md`.
- Em rotas, permissões, autenticação, entrada de usuários, upload de arquivos, configurações, dependências ou revisões de segurança, leia `.agents/skills/seguranca-owasp/SKILL.md`.
- Ao criar classes que demonstram os pilares de POO, siga `docs/poo.md`.

# Outros documentos

- Documento de requisitos completo (disciplina de Engenharia de Software): `docs/requisitos/`. É a origem do PRD, mas o PRD é que define o escopo do protótipo.
- Requisitos do produto: `docs/prd/`. Antes de criar ou alterar, leia `.agents/skills/prd/SKILL.md`.
- Especificações: `docs/specs/`. Antes de criar ou alterar, leia `.agents/skills/spec/SKILL.md`.
- Decisões de arquitetura: `docs/adr/`. Antes de criar ou alterar, leia `.agents/skills/adr/SKILL.md`.
- Scripts SQL entregues à disciplina de Banco de Dados: `banco/`.
