# Mapeamento de Caminhabilidade Urbana

Protótipo de um sistema que mostra em um mapa as condições das calçadas de Maceió, trecho a trecho, para que pessoas com mobilidade reduzida saibam, antes de sair, se o caminho a pé é transitável. A equipe mantém a base de trechos, e os usuários a atualizam enviando feedbacks com foto, que a equipe analisa.

Projeto integrado das disciplinas de Engenharia de Software, Laboratório de Programação e Laboratório de Banco de Dados — Centro Universitário Cesmac, 2026.2.

**Equipe:** Davi Cavalcante Gomes de Castro Duarte e Pedro Henrique Luz Pereira Palmeira.

> Este é um **protótipo minimamente funcional**, feito para demonstrar as funcionalidades reais do sistema. O escopo está no [PRD](docs/prd/0001-caminhabilidade-urbana.md), e o documento de requisitos completo está em [`docs/requisitos/`](docs/requisitos/).

## Tecnologias

Python 3.12+, Django 6.1, PostgreSQL 16+, Leaflet com OpenStreetMap. Site responsivo, pensado para celular.

## Documentação

| Pasta / arquivo | Conteúdo |
|---|---|
| [`docs/prd/`](docs/prd/) | Requisitos do protótipo |
| [`docs/arquitetura.md`](docs/arquitetura.md) | Regras de cada camada |
| [`docs/adr/`](docs/adr/) | Decisões de arquitetura e seus motivos |
| [`docs/specs/`](docs/specs/) | Especificação de cada funcionalidade, na ordem de implementação |
| [`docs/poo.md`](docs/poo.md) | Onde está cada pilar de POO no código |
| [`docs/prompts.md`](docs/prompts.md) | Registro dos prompts e modelos de IA usados |
| [`docs/state.md`](docs/state.md) | Estado atual do trabalho |
| [`.agents/skills/`](.agents/skills/) | Skills usadas pela IA |
| [`banco/`](banco/) | Scripts SQL entregues à disciplina de Banco de Dados |

---

## Como rodar (Windows)

### 1. Instalar

- [Python 3.12 ou superior](https://www.python.org/downloads/) (marque "Add python.exe to PATH").
- [PostgreSQL 16 ou superior](https://www.postgresql.org/download/windows/), com o pgAdmin. Anote a senha do usuário `postgres`.
- Git e VS Code.

### 2. Criar o banco

Edite a senha em `banco/01_criar_banco.sql` e execute-o como `postgres`, pelo Query Tool do pgAdmin (conectado ao banco `postgres`) ou pelo terminal:

```powershell
psql -U postgres -f banco/01_criar_banco.sql
```

### 3. Preparar o projeto

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Preencha o `.env`: `DJANGO_SECRET_KEY` (gere com `python -c "import secrets; print(secrets.token_urlsafe(50))"`) e `DB_PASSWORD` com a senha escolhida no passo 2.

### 4. Depois da spec 0001 implementada

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Depois da spec 0004: `python manage.py carregar_trechos --exemplo --admin <e-mail do superusuário>`.

Depois das migrações, contas e permissões: `psql -U postgres -d caminhabilidade -f banco/02_permissoes.sql` (spec 0008).

Para testar no celular, na mesma rede Wi-Fi: `python manage.py runserver 0.0.0.0:8000` e acesse `http://<IP do computador>:8000`. A localização do navegador só funciona em `localhost` ou HTTPS; pelo IP, o mapa abre no centro de Maceió.

### Testes

```powershell
python manage.py test
```

---

## Roteiro de implementação com IA

Cada spec é uma tarefa. Para cada uma, o ciclo é:

1. **Ler a spec** com a dupla e corrigir o que for preciso **antes** de pedir o código.
2. **Pedir a implementação** (prompt abaixo).
3. **Rodar** `python manage.py test` e testar no navegador, inclusive com a janela estreita (modo celular do DevTools: F12 → Ctrl+Shift+M).
4. **Revisar o diff:** quem não implementou lê o código e pergunta "por que isso está aqui?". Se ninguém souber responder, peça à IA para explicar antes do commit.
5. **Commit** com a mensagem `spec 000X: <título>`.
6. **Conferir** se a IA atualizou `docs/state.md`, `docs/poo.md` e `docs/prompts.md`, e completar a "Revisão da dupla" no `prompts.md`.

### Prompt padrão

```text
Leia o AGENTS.md e implemente a spec docs/specs/000X-<nome>.md, seguindo docs/arquitetura.md e as skills indicadas.
Implemente apenas esta spec. Escreva os testes listados nela e rode python manage.py test até passar.
Ao final, marque os testes cumpridos e o status da spec, atualize docs/state.md, docs/poo.md e docs/prompts.md,
e me mostre um resumo do que foi criado, arquivo por arquivo, explicando as decisões principais.
```

### Ordem

| # | Spec | Requisitos | Sugestão de responsável |
|---|---|---|---|
| 1 | [0001 Fundação](docs/specs/0001-fundacao.md) | RNFs | Davi e Pedro juntos |
| 2 | [0002 Contas](docs/specs/0002-contas.md) | RF-01 a RF-08 | Pedro |
| 3 | [0003 Modelo de dados](docs/specs/0003-modelo-de-dados.md) | Banco | Davi |
| 4 | [0004 Gestão de trechos](docs/specs/0004-gestao-de-trechos.md) | RF-27 a RF-31 | Davi |
| 5 | [0005 Mapa e detalhes](docs/specs/0005-mapa-e-detalhes.md) | RF-09 a RF-17 | Pedro |
| 6 | [0006 Feedbacks](docs/specs/0006-feedbacks.md) | RF-18 a RF-26 | Pedro |
| 7 | [0007 Análise de feedbacks](docs/specs/0007-analise-de-feedbacks.md) | RF-32 a RF-34 | Davi |
| 8 | [0008 Banco: permissões e exportação](docs/specs/0008-banco-permissoes-e-exportacao.md) | Banco | Davi |

As specs 0002 e 0003 podem ser feitas em paralelo (cada uma em sua branch), assim como 0004 e 0005 depois da 0003. Façam o merge na `main` ao fim de cada uma.

### Se faltar tempo

O mínimo exigido são 7 funcionalidades. As specs 0001 a 0007 entregam 10 (cadastro, autenticação, mapa, busca, detalhes, ouvir, enviar feedback, meus feedbacks, gestão de trechos e análise). Se for preciso cortar, cortem nesta ordem: o mapa clicável do formulário de trecho (spec 0004), a importação por CSV (spec 0004) e as notificações (specs 0006 e 0007), registrando o corte no PRD em "Fora do escopo".
