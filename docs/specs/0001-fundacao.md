# Spec 0001: Fundação do projeto

- **Status:** Implementado
- **Requisitos:** RNF-01, RNF-02, RNF-03, RNF-04 e RNF-07 do [PRD 0001](../prd/0001-caminhabilidade-urbana.md)
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-service.md), [ADR 0002](../adr/0002-usuario-customizado-com-login-por-email.md), [ADR 0003](../adr/0003-site-web-responsivo.md), [ADR 0004](../adr/0004-postgresql-como-banco-de-dados.md)

Esta especificação deve ser implementada primeiro. O model `contas.Usuario` precisa existir antes do primeiro `migrate`.

Pré-requisito, feito pela equipe antes desta spec: PostgreSQL instalado, `banco/01_criar_banco.sql` executado, ambiente virtual criado, `pip install -r requirements.txt` executado e `.env` preenchido.

## Criação do projeto

Na raiz do repositório:

```bash
django-admin startproject core .
python manage.py startapp comum
python manage.py startapp contas
python manage.py startapp trechos
python manage.py startapp feedbacks
```

Em cada app, troque os módulos `models.py`, `views.py` e `tests.py` pelos pacotes `models/`, `views/`, `services/`, `forms/` e `tests/` (crie apenas os que a app usar). Cada pacote reexporta suas classes públicas no `__init__.py`.

## Configurações (`core/settings.py`)

| Configuração | Valor |
|---|---|
| Carregamento do `.env` | `load_dotenv(BASE_DIR / ".env")` no início do arquivo |
| `SECRET_KEY` | Variável `DJANGO_SECRET_KEY`. Sem ela, usa uma chave temporária apenas se `DEBUG` for verdadeiro |
| `DEBUG` | Variável `DJANGO_DEBUG` (`"True"` → verdadeiro). Padrão: falso |
| `ALLOWED_HOSTS` | `["localhost", "127.0.0.1"]` e, com `DEBUG`, também `["*"]` para testar no celular na mesma rede |
| `INSTALLED_APPS` | Adicionar `"comum"`, `"contas"`, `"trechos"` e `"feedbacks"` |
| `DATABASES["default"]` | `ENGINE = "django.db.backends.postgresql"`, com `NAME`, `USER`, `PASSWORD`, `HOST` e `PORT` vindos de `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` e `DB_PORT` |
| `AUTH_USER_MODEL` | `"contas.Usuario"` |
| `LOGIN_URL` | `"contas:entrar"` |
| `LOGIN_REDIRECT_URL` | `"trechos:mapa"` |
| `LANGUAGE_CODE` | `"pt-br"` |
| `TIME_ZONE` | `"America/Maceio"` |
| `TEMPLATES[0]["DIRS"]` | `[BASE_DIR / "templates"]` |
| `STATICFILES_DIRS` | `[BASE_DIR / "static"]` |
| `MEDIA_URL` / `MEDIA_ROOT` | `"/media/"` / `BASE_DIR / "media"`. Em `DEBUG`, `core/urls.py` serve os arquivos de mídia |
| `DATA_UPLOAD_MAX_MEMORY_SIZE` | 5 MB |
| `ENVIADOR_DE_CODIGO` | `"contas.services.enviadores.EnviadorSmsSimulado"` ([ADR 0005](../adr/0005-sms-simulado.md)) |
| `LOGGING` | Logger `contas.sms` com saída no console, nível `INFO` |

## App `comum`

### `comum/models/base.py`

```python
class ModeloComDatas(models.Model):
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

Classe abstrata: não gera tabela. Os models que precisam das datas herdam dela ([pilar de herança](../poo.md)).

### `comum/mixins.py`

`AdministradorRequeridoMixin(LoginRequiredMixin, UserPassesTestMixin)`: `test_func` retorna `self.request.user.is_staff`. Visitante é redirecionado para o login; usuário comum autenticado recebe 403.

### `comum/geo.py`

`distancia_em_metros(lat1, lng1, lat2, lng2) -> float`: fórmula de Haversine, com raio da Terra de 6.371.000 m. Aceita `float` ou `Decimal`.

## Model `contas.Usuario` (`contas/models/usuario.py`)

Herda de `AbstractUser` ([ADR 0002](../adr/0002-usuario-customizado-com-login-por-email.md)).

| Campo | Tipo | Regras |
|---|---|---|
| `username` | — | Removido (`username = None`) |
| `email` | `EmailField(max_length=200, unique=True)` | Usado no login (`USERNAME_FIELD`) |
| `nome_completo` | `CharField(max_length=120)` | Obrigatório |
| `celular` | `CharField(max_length=11, unique=True)` | Apenas dígitos: DDD + 9 + 8 dígitos |
| `locomocao` | `CharField(max_length=30)` com `TextChoices` `Locomocao` | `CADEIRA_DE_RODAS`, `ANDADOR_BENGALA_MULETA`, `DEFICIENCIA_VISUAL`, `CARRINHO_DE_BEBE`, `SEM_DIFICULDADE`, `NAO_INFORMADO` (padrão) |
| `celular_verificado` | `BooleanField(default=False)` | |
| `termos_aceitos_em` | `DateTimeField(null=True)` | Preenchido no cadastro |

- `REQUIRED_FIELDS = ["nome_completo", "celular"]`.
- `objects = UsuarioManager()`, com `create_user(email, senha, **campos)` e `create_superuser(...)`. O superusuário é criado com `is_staff`, `is_superuser`, `is_active` e `celular_verificado` verdadeiros.
- `Meta.db_table = "usuario"`.
- Constraints (ver [skill postgresql](../../.agents/skills/postgresql/SKILL.md)):
  - `ck_usuario_celular_formato`: `celular` casa com `^[0-9]{2}9[0-9]{8}$`.
  - `ck_usuario_nome_minimo`: nome com pelo menos 3 caracteres.
  - `ck_usuario_locomocao_valida`: `locomocao` dentro das opções.
  - `ck_usuario_ativo_exige_verificacao`: `is_active` falso **ou** `celular_verificado` verdadeiro.
- `__str__` retorna o e-mail.

Registrar no Admin com uma subclasse de `UserAdmin` ajustada para os campos acima.

## Estrutura de pastas

```text
core/            settings.py, urls.py
comum/           models/base.py, mixins.py, geo.py, tests/
contas/          models/, services/, forms/, views/, templates/contas/, tests/, exceptions.py, urls.py
trechos/         models/, services/, forms/, views/, templates/trechos/, management/commands/, tests/, exceptions.py, urls.py
feedbacks/       models/, services/, forms/, views/, templates/feedbacks/, tests/, exceptions.py, urls.py
templates/base.html
static/css/site.css
static/js/
banco/
```

## Layout base (`templates/base.html`)

Todas as páginas herdam deste template, que contém:

- `<html lang="pt-br">`, `<meta name="viewport" content="width=device-width, initial-scale=1">` e um link "Pular para o conteúdo".
- Cabeçalho com o nome do sistema, que leva ao mapa, e um menu que em celular vira um botão "Menu" (`<details>`/`<summary>` ou botão com `aria-expanded`, sem biblioteca).
- Itens do menu: "Mapa" sempre. Visitante: "Entrar" e "Criar conta". Usuário: "Meus feedbacks" e "Sair", este em um formulário POST com `{% csrf_token %}`. Administrador: também "Painel".
- Área de mensagens do framework `django.contrib.messages`, com `role="status"`.
- Blocos `title`, `extra_head` (para o CSS do Leaflet), `content` e `extra_js`.

## CSS (`static/css/site.css`)

- Escrito primeiro para celular, com `min-width` nas media queries (ex.: 768 px).
- Fonte do sistema, tamanho base de 16 px, áreas de toque com pelo menos 44 × 44 px e foco visível.
- Variáveis CSS para as cores das classificações, reaproveitadas no mapa: Acessível `#1b7f3b`, Parcialmente acessível `#9a6700`, Inacessível `#c62828`, Sem avaliação `#6b6b6b`.

## URLs do projeto (`core/urls.py`)

```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("contas.urls")),
    path("", include("trechos.urls")),
    path("", include("feedbacks.urls")),
]
```

Enquanto uma app não tiver rotas, seu `urls.py` existe com `urlpatterns = []`.

## Teste de arquitetura (`comum/tests/test_arquitetura.py`)

Percorre os módulos de `contas.views`, `trechos.views` e `feedbacks.views` e falha se:

1. uma classe definida no módulo com nome terminado em `View` não tiver `django.views.View` em sua cadeia de herança (`issubclass`), sendo os mixins permitidos;
2. algum padrão de URL do projeto, fora as rotas do Admin e de mídia, não apontar para uma view criada com `as_view()`.

## Testes

- [x] `distancia_em_metros` retorna 0 para o mesmo ponto e cerca de 111 km para 1 grau de latitude.
- [x] `AdministradorRequeridoMixin`: visitante é redirecionado ao login, usuário comum recebe 403 e administrador acessa.
- [x] `create_user` cria usuário inativo e não verificado; `create_superuser` cria ativo e verificado.
- [x] O banco rejeita celular fora do formato e usuário ativo sem celular verificado (`IntegrityError`).
- [x] O teste de arquitetura passa.

## Critérios de aceite

- [x] `python manage.py check` não reporta problemas.
- [x] `python manage.py migrate` executa no PostgreSQL usando `contas.Usuario`.
- [x] `python manage.py createsuperuser` funciona pedindo e-mail, nome completo e celular.
- [x] A página base abre em 360 px de largura sem rolagem horizontal.
