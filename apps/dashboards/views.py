from django.db.models import Count
from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _
from apps.medical.models import MainPageBanner, DoctorAInfo, ContactPhone, News, SiteSettings



class DashboardsView(TemplateView):
    template_name = "views/main-dashboard.html"

    def get_context_data(self, **kwargs):
        """ Asosiy sahifa uchun barcha ma'lumotlarni olish """
        context = super().get_context_data(**kwargs)
        return context


class NewsView(TemplateView):
    template_name = "views/news-dashboard.html"

    def get_context_data(self, **kwargs):
        """ Asosiy sahifa uchun barcha ma'lumotlarni olish """
        context = super().get_context_data(**kwargs)

        # 📌 Oxirgi 4 ta yangilikni olish
        latest_news = News.objects.filter(is_published=True).order_by('-published_date')[:4]

        # 📌 Oylik yangiliklar sonini hisoblash
        monthly_news_counts = (
            News.objects.filter(is_published=True)
            .values('published_date__month')
            .annotate(count=Count('id'))
            .order_by('-published_date__month')
        )

        # 📌 O'zbekcha oy nomlari
        MONTH_NAMES = {
            1: _("Yanvar"),
            2: _("Fevral"),
            3: _("Mart"),
            4: _("Aprel"),
            5: _("May"),
            6: _("Iyun"),
            7: _("Iyul"),
            8: _("Avgust"),
            9: _("Sentabr"),
            10: _("Oktabr"),
            11: _("Noyabr"),
            12: _("Dekabr"),
        }

        # 📌 Oylik yangiliklar sonini o'zbekcha formatda chiqarish
        monthly_news_data = [
            {"month": MONTH_NAMES.get(entry['published_date__month'], "Noma'lum"),
             "count": entry["count"],
             "month_number": entry['published_date__month']}
            for entry in monthly_news_counts
        ]

        context['latest_news'] = latest_news
        context['monthly_news_data'] = monthly_news_data  # 📌 Oylik statistikani kontekstga qo'shish

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