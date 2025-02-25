

import json
from django.conf import settings
from django.utils.translation import get_language

from apps.medical.models import SiteSettings, MainPageBanner, DoctorAInfo, ContactPhone, News
from members.models import CustomUser


def global_context(request):
    """ Barcha sahifalar uchun umumiy ma'lumotlarni qo'shish """

    # 1️⃣ Sayt sozlamalari
    site_settings = SiteSettings.objects.first()

    # 2️⃣ Asosiy bannerlar
    banners = MainPageBanner.objects.all()

    # 3️⃣ Doctor A haqida ma'lumotlar (faqat 3 ta)
    doctor_info_list = DoctorAInfo.objects.order_by('-created_at')[:3]

    # 4️⃣ Aloqa telefonlari
    contact_phones = ContactPhone.objects.all()

    # 5️⃣ Tillar ma'lumotlari
    languages = settings.LANGUAGES

    # 6️⃣ Joriy tilni olish
    current_language = get_language()

    # 7️⃣ JSON formatda tillar ma'lumotlari
    languages_list = [(code, str(name)) for code, name in settings.LANGUAGES]
    languages_json = json.dumps(languages_list)

    # 8️⃣ Oxirgi 5 ta yangilik
    latest_news = News.objects.filter(is_published=True).order_by('-published_date')[:5]

    # 9️⃣ SuperAdmin bo'lmagan oxirgi 4 ta foydalanuvchi
    recent_users = CustomUser.objects.exclude(is_superuser=True).order_by('-date_joined')[:4]

    return {
        "site_settings": site_settings,
        "banners": banners,
        "doctor_info_list": doctor_info_list,
        "contact_phones": contact_phones,
        "LANGUAGES": languages,
        "CURRENT_LANGUAGE": current_language,
        "LANGUAGES_JSON": languages_json,
        "latest_news": latest_news,
        "employees": recent_users,
    }
