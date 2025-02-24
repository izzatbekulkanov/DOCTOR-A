from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.conf import settings
import json

from apps.medical.models import MainPageBanner, DoctorAInfo, ContactPhone, News

from django.utils.translation import get_language
from django.conf import settings

from members.models import CustomUser


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
        current_language = get_language()
        context["CURRENT_LANGUAGE"] = current_language

        # 6️⃣ JSON formatda tillar ma'lumotlari
        languages_list = [(code, str(name)) for code, name in settings.LANGUAGES]
        context["LANGUAGES_JSON"] = json.dumps(languages_list)

        # 7️⃣ Oxirgi 5 ta yangilik
        context["latest_news"] = News.objects.filter(is_published=True).order_by('-published_date')[:5]

        # 8️⃣ SuperAdmin bo'lmagan oxirgi 4 ta foydalanuvchi
        context["recent_users"] = CustomUser.objects.exclude(is_superuser=True).order_by('-date_joined')[:4]

        return context

class NewsView(TemplateView):
    template_name = "views/news-dashboard.html"

    def get_context_data(self, **kwargs):
        """ Asosiy sahifa uchun barcha ma'lumotlarni olish """
        context = super().get_context_data(**kwargs)


        return context

class AnnouncementView(TemplateView):
    template_name = "views/announcement-dashboard.html"

    def get_context_data(self, **kwargs):
        """ Asosiy sahifa uchun barcha ma'lumotlarni olish """
        context = super().get_context_data(**kwargs)


        return context

class EmployeeView(TemplateView):
    template_name = "views/employee-dashboard.html"

    def get_context_data(self, **kwargs):
        """ Asosiy sahifa uchun barcha ma'lumotlarni olish """
        context = super().get_context_data(**kwargs)


        return context

class VideosView(TemplateView):
    template_name = "views/videos-dashboard.html"

    def get_context_data(self, **kwargs):
        """ Asosiy sahifa uchun barcha ma'lumotlarni olish """
        context = super().get_context_data(**kwargs)


        return context