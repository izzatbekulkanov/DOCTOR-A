from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.conf import settings
import json

from apps.medical.models import MainPageBanner, DoctorAInfo, ContactPhone


from django.utils.translation import get_language
from django.conf import settings

class DashboardsView(TemplateView):
    template_name = "views/main-dashboard.html"

    def get_context_data(self, **kwargs):
        """ Asosiy sahifa uchun barcha ma'lumotlarni olish """
        context = super().get_context_data(**kwargs)

        # 1️⃣ Asosiy bannerlar
        context["banners"] = MainPageBanner.objects.all()

        # 2️⃣ Doctor A haqida ma'lumotlar (faqat 3 ta)
        context["doctor_info_list"] = DoctorAInfo.objects.order_by('-created_at')[:3]

        # 3️⃣ Aloqa telefonlari
        context["contact_phones"] = ContactPhone.objects.all()

        # 4️⃣ Tillar ma'lumotlari
        context["LANGUAGES"] = settings.LANGUAGES  # 🔹 Django settings ichidagi tillar

        # 5️⃣ Joriy tilni olish
        context["CURRENT_LANGUAGE"] = get_language()

        # 6️⃣ JSON formatda tillar ma'lumotlari
        languages_list = [(code, str(name)) for code, name in settings.LANGUAGES]
        context["LANGUAGES_JSON"] = json.dumps(languages_list)

        return context
