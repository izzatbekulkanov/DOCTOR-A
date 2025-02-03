import os
from pathlib import Path

from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv


# 📌 `.env` fayldagi muhit o'zgaruvchilarini yuklash
load_dotenv()

# 📌 **Loyiha asosiy katalogi (`BASE_DIR`)**
# Loyiha joylashgan asosiy papkani avtomatik aniqlaydi
BASE_DIR = Path(__file__).resolve().parent.parent


# 🔹 **Xavfsizlik (Security)**
# 📌 **Maxfiy kalit (`SECRET_KEY`)** – Django tomonidan ishlatiladi, `.env` faylda saqlanadi.
SECRET_KEY = os.environ.get("SECRET_KEY", default='')

# 📌 **Ishlab chiqish (`DEBUG`) rejimi**
# Agar `DEBUG=True` bo‘lsa, xatolar ko‘rsatiladi (faqat dev uchun).
DEBUG = os.environ.get("DEBUG", 'True').lower() in ['true', 'yes', '1']

# 📌 **Ruxsat etilgan hostlar (`ALLOWED_HOSTS`)**
# Server ishlashi uchun qabul qilinadigan domen yoki IP manzillar
ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1"]

# 📌 **Joriy muhit (`ENVIRONMENT`)**
# Django qaysi muhitda ishlayotganini aniqlaydi: `local`, `staging`, `production`
ENVIRONMENT = os.environ.get("DJANGO_ENVIRONMENT", default="local")


# 🔹 **Django ilovalari (`INSTALLED_APPS`)**
# 📌 Bu yerda barcha ilovalar (apps) ro'yxati keltirilgan
LOCAL_APPS = [
    # 📌 **Loyiha ichidagi ilovalar**
    "apps.dashboards",   # Dashboard ilovasi
    "apps.medical",  # ✅ Yangi `medical` ilovasini qo‘shdik
    "apps.auth",  # ✅ `apps.auth` ilovasi to‘g‘ri chaqirilgan
    "apps.logs",  # Loglar
    "apps.bot",  # Telegram bot uchun
    "apps.common",  # Templatetaglar uchun
    "members",  # Foydalanuvchilar
]
DYNAMIC_APPS = [
    "django.contrib.admin",  # Django admin paneli
    "django.contrib.auth",  # Auth (foydalanuvchilarni boshqarish)
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'django_json_widget',
]


# 📌 **Custom foydalanuvchi modeli (`AUTH_USER_MODEL`)**
AUTH_USER_MODEL = "members.CustomUser"  # ✅ To‘g‘ri yozish


INSTALLED_APPS = LOCAL_APPS + DYNAMIC_APPS

# 🔹 **Middleware (`MIDDLEWARE`)**
# 📌 Django request va response (so‘rov va javob) o‘rtasida ishlov beruvchi vositalar.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # 📌 Statik fayllarni tezroq xizmat ko'rsatish uchun
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware", # 📌 Til o‘zgarishlari uchun middleware
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
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",  # 📌 SQLite bazasi (default)
        "NAME": BASE_DIR / "db.sqlite3",  # 📌 Baza nomi (lokal)
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


# 🔹 **Til sozlamalari (`LANGUAGES` va `LANGUAGE_CODE`)**
LANGUAGES = [
    ("uz", _("O'zbek")),
    ("ru", _("Русский")),
    ("en", _("English")),
    ("de", _("Deutsch")),
    ("tr", _("Türkçe")),
]

LANGUAGE_CODE = "uz"  # 📌 Standart til - O'zbek tili

# 🔹 **Vaqt zonasi (`TIME_ZONE`)**
TIME_ZONE = "Asia/Tashkent"  # 📌 Toshkent vaqti

USE_I18N = True  # 📌 Tillarni qo‘llab-quvvatlash
USE_TZ = True  # 📌 Django vaqtni `timezone-aware` qilish

# 🔹 **Til fayllar joylashgan katalog (`LOCALE_PATHS`)**
LOCALE_PATHS = [BASE_DIR / "locale"]


# 📌 Statik fayllar sozlamalari
STATIC_URL = "/static/"  # Statik fayllarning URL yo‘li
STATIC_ROOT = BASE_DIR / "staticfiles"  # Statik fayllar yig‘iladigan joy
STATICFILES_DIRS = [
    BASE_DIR / "src" / "assets",  # Statik fayllarning asosiy manbasi
]

# 📌 Media fayllar (foydalanuvchi yuklagan fayllar)
MEDIA_URL = "/media/"  # Media fayllarning URL yo‘li
MEDIA_ROOT = BASE_DIR / "media"  # Media fayllar saqlanadigan katalog

# 🔹 **Saytning asosiy URL manzili (`BASE_URL`)**
BASE_URL = os.environ.get("BASE_URL", default="http://127.0.0.1:8000")


# 🔹 **Model ID generatsiyasi (`DEFAULT_AUTO_FIELD`)**
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"



# 🔹 **Login va Logout sozlamalari**
LOGIN_URL = "/login/"  # 📌 Agar foydalanuvchi login qilmagan bo‘lsa, shu sahifaga yo‘naltiriladi
LOGOUT_REDIRECT_URL = "/login/"  # 📌 Logout bo‘lgandan keyin qayta yo‘naltiriladi


# 🔹 **Session sozlamalari**
SESSION_ENGINE = "django.contrib.sessions.backends.db"  # 📌 Sessionlar bazada saqlanadi
SESSION_COOKIE_SECURE = True  # 📌 HTTPS orqali cookie'lar yuboriladi
SESSION_COOKIE_HTTPONLY = True  # 📌 JavaScript session cookie'ni ko‘ra olmaydi
SESSION_COOKIE_SAMESITE = "Lax"  # 📌 Xavfsizlik sozlamasi

SESSION_COOKIE_AGE = 3600  # 📌 Sessiyaning amal qilish vaqti (1 soat)

# 🔹 **CSRF Trusted Origins**
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5050",
]
