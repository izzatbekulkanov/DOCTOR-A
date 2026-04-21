import json

from django.conf import settings
from django.utils.translation import get_language

from apps.medical.models import (
    ClinicService,
    ContactPhone,
    DoctorAInfo,
    MainPageBanner,
    Partner,
    SiteSettings,
)
from apps.members.models import CustomUser
from apps.news.models import Announcement, News


FOOTER_RICH_TEXT_TRANSLATIONS = {
    "working_hours": {
        "uz": "<p>Dushanba - Shanba: 08:00 - 16:00</p><p>Yakshanba: Dam olish kuni</p><p><strong>24/7 Xizmatlar:</strong> MRT, MSKT, Rentgen, LOR</p>",
        "ru": "<p>Понедельник - Суббота: 08:00 - 16:00</p><p>Воскресенье: Выходной день</p><p><strong>Услуги 24/7:</strong> МРТ, МСКТ, Рентген, ЛОР</p>",
        "en": "<p>Monday - Saturday: 08:00 - 16:00</p><p>Sunday: Day off</p><p><strong>24/7 Services:</strong> MRI, MSCT, X-ray, ENT</p>",
        "de": "<p>Montag - Samstag: 08:00 - 16:00</p><p>Sonntag: Ruhetag</p><p><strong>24/7-Leistungen:</strong> MRT, MSKT, Rontgen, HNO</p>",
        "tr": "<p>Pazartesi - Cumartesi: 08:00 - 16:00</p><p>Pazar: Tatil gunu</p><p><strong>7/24 Hizmetler:</strong> MRG, MSCT, Rontgen, KBB</p>",
    },
    "address": {
        "uz": "<p>Manzil: Namangan shahri, Boburshoh ko'chasi, 2-uy.</p><p>Mo'ljal: Jahon (Lola) bozori, NamDU qoshidagi akademik litsey.</p><p>Yana bir filial: Irvadon MFY, Namangan ko'chasi, 2-uy.</p>",
        "ru": "<p>Адрес: г. Наманган, улица Бобуршох, дом 2.</p><p>Ориентир: рынок Jahon (Lola), академический лицей при NamDU.</p><p>Дополнительный филиал: МФЙ Ирвадон, улица Наманган, дом 2.</p>",
        "en": "<p>Address: 2 Boburshoh Street, Namangan city.</p><p>Landmark: Jahon (Lola) market, the academic lyceum near NamDU.</p><p>Additional branch: Irvadon neighborhood, 2 Namangan Street.</p>",
        "de": "<p>Adresse: Boburshoh-Strasse 2, Namangan.</p><p>Orientierungspunkt: Jahon-(Lola)-Markt, akademisches Lyzeum bei NamDU.</p><p>Zusatzliche Filiale: MFY Irvadon, Namangan-Strasse 2.</p>",
        "tr": "<p>Adres: Namangan sehri, Boburshoh Caddesi 2 numara.</p><p>Referans nokta: Jahon (Lola) pazari, NamDU yanindaki akademik lise.</p><p>Ek sube: Irvadon mahallesi, Namangan Caddesi 2 numara.</p>",
    },
}


def _translate_footer_value(values, language_code):
    normalized_language = (language_code or "uz").split("-")[0].lower()
    return (
        values.get(normalized_language)
        or values.get("uz")
        or values.get("en")
        or next(iter(values.values()), "")
    )


def _resolve_footer_rich_text(value, language_code, fallback_key):
    if isinstance(value, dict):
        resolved = _translate_footer_value(value, language_code)
        if resolved:
            return resolved

    if isinstance(value, str):
        normalized_value = value.strip()
        if normalized_value:
            if normalized_value.startswith("{") and normalized_value.endswith("}"):
                try:
                    parsed_value = json.loads(normalized_value)
                except json.JSONDecodeError:
                    parsed_value = None
                if isinstance(parsed_value, dict):
                    resolved = _translate_footer_value(parsed_value, language_code)
                    if resolved:
                        return resolved
            if (language_code or "uz").split("-")[0].lower() == "uz":
                return normalized_value

    return _translate_footer_value(FOOTER_RICH_TEXT_TRANSLATIONS[fallback_key], language_code)


def global_context(request):
    site_settings = SiteSettings.objects.first()
    banner = MainPageBanner.objects.last()
    doctor_info_list = DoctorAInfo.objects.order_by("-created_at")[:3]
    contact_phones = ContactPhone.objects.all()
    languages = settings.LANGUAGES
    current_language = get_language()
    languages_list = [(code, str(name)) for code, name in settings.LANGUAGES]
    languages_json = json.dumps(languages_list)
    latest_news = News.objects.filter(is_published=True).order_by("-published_date")[:2]
    latest_announcements = Announcement.objects.filter(is_published=True).order_by("-published_date")[:2]
    recent_users = CustomUser.objects.exclude(is_superuser=True).order_by("-date_joined")[:4]
    active_partners = Partner.objects.filter(is_active=True).order_by("-created_at")
    footer_services = ClinicService.objects.filter(is_active=True).order_by("sort_order", "id")[:6]
    footer_content = {
        "working_hours_html": _resolve_footer_rich_text(
            site_settings.working_hours if site_settings else "",
            current_language,
            "working_hours",
        ),
        "address_html": _resolve_footer_rich_text(
            site_settings.address if site_settings else "",
            current_language,
            "address",
        ),
    }

    return {
        "site_settings": site_settings,
        "banner": banner,
        "doctor_info_list": doctor_info_list,
        "contact_phones": contact_phones,
        "LANGUAGES": languages,
        "CURRENT_LANGUAGE": current_language,
        "LANGUAGES_JSON": languages_json,
        "latest_news": latest_news,
        "latest_announcements": latest_announcements,
        "employees": recent_users,
        "active_partners": active_partners,
        "footer_services": footer_services,
        "footer_content": footer_content,
    }
