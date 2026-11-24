"""Configurações do projeto Caminhabilidade Urbana (spec 0001).

Segredos e dados de conexão vêm do arquivo .env (veja .env.example).
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# Segurança

DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("Defina DJANGO_SECRET_KEY no .env quando DEBUG for falso.")
    # Chave temporária só para desenvolvimento: muda a cada execução e derruba as sessões.
    SECRET_KEY = get_random_secret_key()

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
if DEBUG:
    # Permite abrir o site pelo IP da máquina no celular, na mesma rede.
    ALLOWED_HOSTS += ["*"]


# Aplicações

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "comum",
    "contas",
    "trechos",
    "feedbacks",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "feedbacks.context_processors.notificacoes",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# Banco de dados (ADR 0004)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "caminhabilidade"),
        "USER": os.environ.get("DB_USER", "caminhabilidade_owner"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}


# Autenticação (ADR 0002)

AUTH_USER_MODEL = "contas.Usuario"
LOGIN_URL = "contas:entrar"
LOGIN_REDIRECT_URL = "trechos:mapa"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internacionalização

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Maceio"
USE_I18N = True
USE_TZ = True


# Arquivos estáticos e de mídia

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024


# Envio do código de verificação (ADR 0005, implementado na spec 0002)

ENVIADOR_DE_CODIGO = "contas.services.enviadores.EnviadorSmsSimulado"


# Registro de eventos

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "contas.sms": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


# E-mail (não usado pelo protótipo; mantido no console para não enviar nada)

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}
