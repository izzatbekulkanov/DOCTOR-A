import os
from pathlib import Path
from dotenv import load_dotenv
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent
# ✅ Load .env from BASE_DIR
load_dotenv(dotenv_path=os.path.join(BASE_DIR, '.env'))

SECRET_KEY = os.environ.get("SECRET_KEY", default='unsafe-secret-key')

DEBUG = os.environ.get("DEBUG", 'True').lower() in ['true', 'yes', '1']


DJANGO_ENVIRONMENT = os.environ.get("DJANGO_ENVIRONMENT")

print("bu environment",DJANGO_ENVIRONMENT)



BASE_URL = os.environ.get("BASE_URL", default='https://webtest.namspi.uz/')

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "")
if isinstance(ALLOWED_HOSTS, str):
    ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS.split(",") if host.strip()]

LOCAL_APPS = [
    "apps.dashboards",
    "apps.medical",
    "apps.auth",
    "apps.logs",
    "apps.bot",
    "apps.common",
    "apps.news",
    "apps.api",
    "members",
]

WEB_APPS = [
    'rest_framework',
]
DYNAMIC_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rosetta",
    'django_json_widget',
]

AUTH_USER_MODEL = "members.CustomUser"

INSTALLED_APPS = LOCAL_APPS + DYNAMIC_APPS + WEB_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # WhiteNoise qo‘shilgan
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'apps.logs.middleware.LogMiddleware',
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    } if DJANGO_ENVIRONMENT == 'local' else {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'doctor_a_db'),
        'USER': os.environ.get('POSTGRES_USER', 'doctor_a_user'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'admin1231'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
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
    ("tr", _("Türkçe")),
]

TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_L10N = True
USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

ROSETTA_SHOW_AT_ADMIN_PANEL = True
ROSETTA_MESSAGES_PER_PAGE = 50
ROSETTA_STORAGE_CLASS = "rosetta.storage.CacheRosettaStorage"
ROSETTA_ACCESS_CONTROL_FUNCTION = None

# Statik fayllar sozlamasi
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'  # WhiteNoise uchun

# Statik fayllar manba papkasi (lokal va productionda ishlatiladi)
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

BASE_URL = os.environ.get("BASE_URL", default="http://127.0.0.1:8000")
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/login/"
LOGOUT_REDIRECT_URL = "/"

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 3600

CSRF_TRUSTED_ORIGINS = [
    "https://*.namspi.uz",
    "https://doctoramedical.uz",
    "https://doctoramedclinic.uz",
]