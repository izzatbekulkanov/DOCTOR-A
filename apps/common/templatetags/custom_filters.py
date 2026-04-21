import json
from django import template
from django.template.defaultfilters import linebreaksbr
from django.utils.html import conditional_escape, strip_tags
from django.utils.safestring import mark_safe

register = template.Library()

UI_LABELS = {
    "call_us": {
        "uz": "Qo'ng'iroq qiling:",
        "ru": "Позвоните нам:",
        "en": "Call Us:",
        "de": "Rufen Sie uns an:",
        "tr": "Bizi Arayın:",
    },
    "email": {
        "uz": "Email:",
        "ru": "Эл. почта:",
        "en": "Email:",
        "de": "E-Mail:",
        "tr": "E-posta:",
    },
    "home": {
        "uz": "Bosh sahifa",
        "ru": "Главная",
        "en": "Home",
        "de": "Startseite",
        "tr": "Ana Sayfa",
    },
    "about": {
        "uz": "Biz haqimizda",
        "ru": "О нас",
        "en": "About Us",
        "de": "Über uns",
        "tr": "Hakkımızda",
    },
    "services": {
        "uz": "Xizmatlar",
        "ru": "Услуги",
        "en": "Services",
        "de": "Leistungen",
        "tr": "Hizmetler",
    },
    "working_hours": {
        "uz": "Ish vaqti",
        "ru": "Р РµР¶РёРј СЂР°Р±РѕС‚С‹",
        "en": "Working Hours",
        "de": "Arbeitszeiten",
        "tr": "Calisma Saatleri",
    },
    "address_landmark": {
        "uz": "Manzil va mo'ljal",
        "ru": "РђРґСЂРµСЃ Рё РѕСЂРёРµРЅС‚РёСЂ",
        "en": "Address and Landmark",
        "de": "Adresse und Orientierungspunkt",
        "tr": "Adres ve Konum Tarifi",
    },
    "phone": {
        "uz": "Telefon",
        "ru": "РўРµР»РµС„РѕРЅ",
        "en": "Phone",
        "de": "Telefon",
        "tr": "Telefon",
    },
    "email_address": {
        "uz": "Elektron pochta",
        "ru": "Р­Р»РµРєС‚СЂРѕРЅРЅР°СЏ РїРѕС‡С‚Р°",
        "en": "Email",
        "de": "E-Mail",
        "tr": "E-posta",
    },
    "contact_us": {
        "uz": "Bog'lanish",
        "ru": "Связаться",
        "en": "Contact Us",
        "de": "Kontakt",
        "tr": "Iletisim",
    },
    "view_services": {
        "uz": "Xizmatlarni ko'rish",
        "ru": "Посмотреть услуги",
        "en": "View Services",
        "de": "Leistungen ansehen",
        "tr": "Hizmetleri Gor",
    },
    "doctors": {
        "uz": "Shifokorlar",
        "ru": "Врачи",
        "en": "Doctors",
        "de": "Ärzte",
        "tr": "Doktorlar",
    },
    "videos": {
        "uz": "Videolar",
        "ru": "Видео",
        "en": "Videos",
        "de": "Videos",
        "tr": "Videolar",
    },
    "equipment": {
        "uz": "Uskunalar",
        "ru": "Оборудование",
        "en": "Equipment",
        "de": "Geräte",
        "tr": "Ekipman",
    },
    "blog": {
        "uz": "Yangiliklar",
        "ru": "Новости",
        "en": "News",
        "de": "Nachrichten",
        "tr": "Haberler",
    },
    "announcements": {
        "uz": "E'lonlar",
        "ru": "Объявления",
        "en": "Announcements",
        "de": "Ankündigungen",
        "tr": "Duyurular",
    },
    "shop_list": {
        "uz": "Uskunalar ro'yxati",
        "ru": "Список оборудования",
        "en": "Shop List",
        "de": "Shop-Liste",
        "tr": "Ekipman Listesi",
    },
    "contact": {
        "uz": "Aloqa",
        "ru": "Контакты",
        "en": "Contact",
        "de": "Kontakt",
        "tr": "İletişim",
    },
    "login": {
        "uz": "Kirish",
        "ru": "Вход",
        "en": "Login",
        "de": "Anmelden",
        "tr": "Giriş",
    },
    "footer_description": {
        "uz": "Namangan shahridagi zamonaviy ko'p tarmoqli tibbiyot markazi. Bizda 24/7 rejimida ishlovchi MRT, MSKT va Rentgen xizmatlari, yuqori aniqlikdagi laboratoriya, UZI hamda kardiologiya, nevrologiya, ginekologiya va jarrohlik kabi 15 dan ortiq ixtisoslashgan yo'nalishlar bo'yicha tajribali shifokorlar yordami ko'rsatiladi.",
        "ru": "современный многопрофильный медицинский центр в городе Наманган. У нас круглосуточно работают МРТ, МСКТ и рентген, доступны высокоточная лаборатория, УЗИ, а также помощь опытных врачей более чем по 15 специализированным направлениям, включая кардиологию, неврологию, гинекологию и хирургию.",
        "en": "is a modern multidisciplinary medical center in Namangan. We provide 24/7 MRI, MSCT, and X-ray services, a high-precision laboratory, ultrasound, and care from experienced doctors across more than 15 specialized fields including cardiology, neurology, gynecology, and surgery.",
        "de": "ist ein modernes interdisziplinäres medizinisches Zentrum in Namangan. Wir bieten rund um die Uhr MRT-, MSCT- und Röntgenleistungen, ein hochpräzises Labor, Ultraschall sowie erfahrene Fachärzte in mehr als 15 spezialisierten Bereichen, darunter Kardiologie, Neurologie, Gynäkologie und Chirurgie.",
        "tr": "Namangan şehrinde bulunan modern çok branşlı bir tıp merkezidir. Merkezimizde 7/24 MR, MSCT ve röntgen hizmetleri, yüksek hassasiyetli laboratuvar, ultrason ve kardiyoloji, nöroloji, jinekoloji ile cerrahi dahil 15'ten fazla uzmanlık alanında deneyimli doktor desteği sunulmaktadır.",
    },
    "welcome_to": {
        "uz": "Salom",
        "ru": "Добро пожаловать в",
        "en": "Welcome To",
        "de": "Willkommen bei",
        "tr": "Hoş Geldiniz",
    }
}

@register.filter
def get_language_text(data, lang_code):
    """
    JSON formatidagi matndan joriy tilga mos keladigan matnni chiqaradi.
    Agar mavjud bo‘lmasa, 'uz' tilidagi matn olinadi.
    """
    if isinstance(data, str):  # JSON string bo'lsa
        try:
            data = json.loads(data)  # JSON formatga o‘tkazamiz
        except json.JSONDecodeError:
            return data  # Agar xatolik bo‘lsa, o‘zini qaytaradi

    if isinstance(data, dict):  # Agar lug‘at bo‘lsa
        return data.get(lang_code, data.get('uz', 'Tavsif mavjud emas'))

    return data  # Agar JSON bo‘lmasa, o‘zini qaytaradi

@register.filter
def get_initials(value):
    if not value:
        return ""
    parts = value.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[-1][0]}".upper()
    return value[:1].upper()

@register.filter
def lookup(value, key):
    if hasattr(value, "get"):
        return value.get(key, '')
    return ''


@register.filter
def render_rich_text(value):
    if value is None:
        return ""

    if not isinstance(value, str):
        return value

    normalized_value = value.strip()
    if not normalized_value:
        return ""

    if strip_tags(normalized_value) != normalized_value:
        return mark_safe(normalized_value)

    return linebreaksbr(conditional_escape(normalized_value))


@register.filter(name='multiply')
def multiply(value, arg):
    """Ikki qiymatni ko'paytiradi."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value  # Agar xatolik yuz bersa, asl qiymatni qaytaradi


@register.simple_tag
def ui_label(key, lang_code="en"):
    labels = UI_LABELS.get(key, {})
    normalized_lang = (lang_code or "en").split("-")[0].lower()
    return labels.get(normalized_lang) or labels.get("en") or key
