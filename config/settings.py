import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
from django.utils.translation import gettext_lazy as _


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    value = os.environ.get(name, default)
    if not value:
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

DJANGO_ENVIRONMENT = (os.environ.get("DJANGO_ENVIRONMENT") or "local").strip().lower()
DEBUG = env_bool("DEBUG", True) if DJANGO_ENVIRONMENT == "local" else False

SECRET_KEY = os.environ.get("SECRET_KEY", "unsafe-secret-key")
BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
BASE_URL_PARTS = urlsplit(BASE_URL)
BASE_ORIGIN = (
    f"{BASE_URL_PARTS.scheme}://{BASE_URL_PARTS.netloc}"
    if BASE_URL_PARTS.scheme and BASE_URL_PARTS.netloc
    else ""
)

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "127.0.0.1,localhost")
if BASE_URL_PARTS.hostname and BASE_URL_PARTS.hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(BASE_URL_PARTS.hostname)
if DEBUG:
    for local_host in ("127.0.0.1", "localhost", "testserver"):
        if local_host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(local_host)

csrf_default = "http://127.0.0.1:8000,http://localhost:8000" if DEBUG else ""
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", csrf_default)
if BASE_ORIGIN and BASE_ORIGIN not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(BASE_ORIGIN)

LOCAL_APPS = [
    "apps.dashboards",
    "apps.medical",
    "apps.auth",
    "apps.logs",
    "apps.bot",
    "apps.common",
    "apps.news",
    "apps.api",
    "apps.members",
]

WEB_APPS = [
    "rest_framework",
]

DYNAMIC_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rosetta",
    "django_json_widget",
]

AUTH_USER_MODEL = "members.CustomUser"
INSTALLED_APPS = LOCAL_APPS + DYNAMIC_APPS + WEB_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "config.middleware.DefaultLocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.logs.middleware.LogMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.dashboards.context_processors.global_context",
            ],
            "builtins": [
                "django.templatetags.static",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

use_sqlite = DJANGO_ENVIRONMENT == "local"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
    if use_sqlite
    else {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "doctor_a_db"),
        "USER": os.environ.get("POSTGRES_USER", "doctor_a_user"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": int(os.environ.get("POSTGRES_CONN_MAX_AGE", "60")),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "uz"
LANGUAGES = [
    ("uz", _("O'zbek")),
    ("ru", _("Русский")),
    ("en", _("English")),
    ("de", _("Deutsch")),
    ("tr", _("Turkce")),
]

TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_L10N = True
USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

ROSETTA_SHOW_AT_ADMIN_PANEL = True
ROSETTA_MESSAGES_PER_PAGE = 50
ROSETTA_STORAGE_CLASS = "rosetta.storage.CacheRosettaStorage"
ROSETTA_ACCESS_CONTROL_FUNCTION = None

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

staticfiles_backend = (
    "django.contrib.staticfiles.storage.StaticFilesStorage"
    if DEBUG or "test" in sys.argv
    else "whitenoise.storage.CompressedManifestStaticFilesStorage"
)

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": staticfiles_backend,
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/login/"
LOGOUT_REDIRECT_URL = "/"

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", not DEBUG)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
SESSION_COOKIE_AGE = int(os.environ.get("SESSION_COOKIE_AGE", "3600"))

CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_HTTPONLY = env_bool("CSRF_COOKIE_HTTPONLY", False)
CSRF_COOKIE_SAMESITE = os.environ.get("CSRF_COOKIE_SAMESITE", "Lax")

USE_X_FORWARDED_HOST = env_bool("USE_X_FORWARDED_HOST", not DEBUG)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", not DEBUG)
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000" if not DEBUG else "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", not DEBUG)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", not DEBUG)
SECURE_CONTENT_TYPE_NOSNIFF = env_bool("SECURE_CONTENT_TYPE_NOSNIFF", True)
SECURE_REFERRER_POLICY = os.environ.get("SECURE_REFERRER_POLICY", "same-origin")
X_FRAME_OPTIONS = os.environ.get("X_FRAME_OPTIONS", "SAMEORIGIN")

TURNSTILE_SITE_KEY = os.environ.get("TURNSTILE_SITE_KEY", "0x4AAAAAADAzCORlE16Oa7ho").strip()
TURNSTILE_SECRET_KEY = os.environ.get("TURNSTILE_SECRET_KEY", "").strip()
TURNSTILE_VERIFY_URL = os.environ.get(
    "TURNSTILE_VERIFY_URL",
    "https://challenges.cloudflare.com/turnstile/v0/siteverify",
).strip()
TURNSTILE_SCRIPT_URL = os.environ.get(
    "TURNSTILE_SCRIPT_URL",
    "https://challenges.cloudflare.com/turnstile/v0/api.js",
).strip()
TURNSTILE_TIMEOUT = int(os.environ.get("TURNSTILE_TIMEOUT", "10"))
TURNSTILE_REQUIRED = env_bool("TURNSTILE_REQUIRED", not DEBUG)
