"""
Django settings for the Kairos portal.

Every machine-specific or secret value comes from environment variables, read from
portal/.env in development (see .env.example). Real environment variables win over .env.
"""

import sys
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent  # portal/
REPO_ROOT = BASE_DIR.parent

# The running-plan engines live at the repo root (shared with the Flask app) and are
# imported unchanged. See portal/ENGINES.md.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")


# Core

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])


# Applications

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # Kairos
    "accounts",
    "core",
    "training",
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

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Project templates win over app templates (incl. Django admin's registration/ pages).
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database: Postgres in Docker for development (portal/docker-compose.yml).
# DATABASE_URL overrides the POSTGRES_* parts (e.g. a managed database in production).

_pg = {
    "user": env("POSTGRES_USER", default="kairos"),
    "password": env("POSTGRES_PASSWORD", default=""),
    # 127.0.0.1, not "localhost": on this machine localhost tries IPv6 ::1 first, which
    # Docker doesn't listen on, and the connection stalls instead of falling back.
    "host": env("POSTGRES_HOST", default="127.0.0.1"),
    "port": env("POSTGRES_PORT", default="5432"),
    "db": env("POSTGRES_DB", default="kairos"),
}
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://{user}:{password}@{host}:{port}/{db}".format(**_pg),
    )
}
# Fail fast (seconds) if the database is down, instead of hanging.
DATABASES["default"].setdefault("OPTIONS", {})["connect_timeout"] = env.int("POSTGRES_CONNECT_TIMEOUT", default=5)


# Auth

# Custom user model from day one: swapping it after the first migration is painful.
AUTH_USER_MODEL = "accounts.User"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization. Stored times are UTC; each client gets their own time zone later.

LANGUAGE_CODE = "en-us"
TIME_ZONE = env("DJANGO_TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True


# Static files

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]  # portal/static/kairos/ = the design system (portal/DESIGN.md)
STATIC_ROOT = BASE_DIR / "staticfiles"


# Email: console backend in development (password reset, inquiry form). Real SMTP comes in Phase 3.

DEFAULT_FROM_EMAIL = env("DJANGO_DEFAULT_FROM_EMAIL", default="Kairos <no-reply@localhost>")

MAILERS = {
    "default": {
        "BACKEND": env(
            "DJANGO_EMAIL_BACKEND",
            default="django.core.mail.backends.console.EmailBackend",
        ),
    },
}
