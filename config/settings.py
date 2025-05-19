import os
from pathlib import Path

from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", default='')

DEBUG = os.environ.get("DEBUG", 'True').lower() in ['true', 'yes', '1']
ENVIRONMENT = 'local'
BASE_URL = os.environ.get("BASE_URL", default='https://webtest.namspi.uz/')

ALLOWED_HOSTS = [
    "localhost",
    "0.0.0.0",
    "127.0.0.1",
    "updatehub.namspi.uz",
    "webtest.namspi.uz",
    "doctoramedical.uz"
]


LOCAL_APPS = [
    # 📌 **Loyiha ichidagi ilovalar**
    "apps.dashboards",  # Dashboard ilovasi
    "apps.medical",  # ✅ Yangi `medical` ilovasini qo‘shdik
    "apps.auth",  # ✅ `apps.auth` ilovasi to‘g‘ri chaqirilgan
    "apps.logs",  # Loglar
    "apps.bot",  # Telegram bot uchun
    "apps.common",  # Templatetaglar uchun
    "apps.news",  # Yangiliklar uchun
    "apps.api",  # API uchun
    "members",  # Foydalanuvchilar

]

WEB_APPS = [
    'rest_framework',
]
DYNAMIC_APPS = [
    "django.contrib.admin",  # Django admin paneli
    "django.contrib.auth",  # Auth (foydalanuvchilarni boshqarish)
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rosetta",  # Tillarni boshqarish uchun
    'django_json_widget',
]

# 📌 **Custom foydalanuvchi modeli (`AUTH_USER_MODEL`)**
AUTH_USER_MODEL = "members.CustomUser"  # ✅ To‘g‘ri yozish

INSTALLED_APPS = LOCAL_APPS + DYNAMIC_APPS + WEB_APPS

# 🔹 **Middleware (`MIDDLEWARE`)**
# 📌 Django request va response (so‘rov va javob) o‘rtasida ishlov beruvchi vositalar.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # 📌 Statik fayllarni tezroq xizmat ko'rsatish uchun
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # 📌 Til o‘zgarishlari uchun middleware
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",  # 📌 CSRF himoyasi
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # 📌 Auth middleware
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",  # 📌 X-Frame Options himoyasi
    'apps.logs.middleware.LogMiddleware',

]

# 🔹 **URL sozlamalari (`ROOT_URLCONF`)**
# 📌 Django loyihasi asosiy `urls.py` faylini ko'rsatadi
ROOT_URLCONF = "config.urls"

# 🔹 **Shablonlar (`TEMPLATES`)**
# 📌 Django templatelari (HTML fayllari) sozlamalari
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # 📌 Template fayllar joylashgan katalog
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

# 🔹 **WSGI sozlamalari (`WSGI_APPLICATION`)**
# 📌 WSGI – Django server uchun asosiy interfeys
WSGI_APPLICATION = "config.wsgi.application"

# 🔹 **Ma’lumotlar bazasi (`DATABASES`)**
# 📌 Django qaysi ma'lumotlar bazasidan foydalanishini ko'rsatadi
# Database configuration
# Ma'lumotlar bazasi sozlamalari
print(f"Current environment: {ENVIRONMENT}")  # Muhitni konsolga chiqarish
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    } if ENVIRONMENT == 'local' else {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'doctor_a_db'),
        'USER': os.environ.get('POSTGRES_USER', 'doctor_a_user'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'admin1231'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

# 🔹 **Parolni tekshirish (`AUTH_PASSWORD_VALIDATORS`)**
# 📌 Foydalanuvchi parolini tekshirish qoidalari
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "uz"  # 📌 Standart til - O'zbek tili
# 🔹 **Til sozlamalari (`LANGUAGES` va `LANGUAGE_CODE`)**
LANGUAGES = [
    ("uz", _("O'zbek")),
    ("ru", _("Русский")),
    ("en", _("English")),
    ("de", _("Deutsch")),
    ("tr", _("Türkçe")),
]



# 🔹 **Vaqt zonasi (`TIME_ZONE`)**
TIME_ZONE = "Asia/Tashkent"  # 📌 Toshkent vaqti

USE_I18N = True  # 📌 Tillarni qo‘llab-quvvatlash
USE_L10N = True
USE_TZ = True  # 📌 Django vaqtni `timezone-aware` qilish

# 🔹 **Til fayllar joylashgan katalog (`LOCALE_PATHS`)**
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

ROSETTA_SHOW_AT_ADMIN_PANEL = True  # Admin panelda Rosetta'ni ko'rsatish
ROSETTA_MESSAGES_PER_PAGE = 50  # Tarjima xabarlari soni
ROSETTA_STORAGE_CLASS = "rosetta.storage.CacheRosettaStorage"  # Tarjima xotirada saqlanadi
ROSETTA_ACCESS_CONTROL_FUNCTION = None  # Maxsus huquqlarni o'chirish


# 📌 Statik fayllar sozlamasi
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # `collectstatic` bu yerni to'ldiradi

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# 📌 DEBUG=True bo'lsa, qo'shimcha static fayllar katalogini qo'shamiz
if DEBUG:
    STATICFILES_DIRS = [BASE_DIR / "src" / "assets"]
else:
    STATICFILES_DIRS = []

# 🔹 **Saytning asosiy URL manzili (`BASE_URL`)**
BASE_URL = os.environ.get("BASE_URL", default="http://127.0.0.1:8000")

# 🔹 **Model ID generatsiyasi (`DEFAULT_AUTO_FIELD`)**
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 🔹 **Login va Logout sozlamalari**
LOGIN_URL = "/login/"  # 📌 Agar foydalanuvchi login qilmagan bo‘lsa, shu sahifaga yo‘naltiriladi
LOGOUT_REDIRECT_URL = "/"  # 📌 Logout bo‘lgandan keyin qayta yo‘naltiriladi

# 🔹 **Session sozlamalari**
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 3600

# 🔹 **CSRF Trusted Origins**
CSRF_TRUSTED_ORIGINS = [
    "https://*.namspi.uz",
    "https://doctoramedical.uz",
]