from django.db.models import Count
from django.http import JsonResponse
from django.views.generic import TemplateView, DetailView
from django.utils.translation import gettext_lazy as _
from apps.medical.models import News, Comment


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


class NewsDetailDashboard(DetailView):
    model = News
    template_name = "views/news-detail-dashboard.html"
    context_object_name = "news"

    def get_context_data(self, **kwargs):
        """ Yangilik tafsilotlarini olish """
        context = super().get_context_data(**kwargs)

        # 📌 O'xshash yangiliklarni olish
        related_news = News.objects.filter(
            is_published=True
        ).exclude(id=self.object.id).order_by('-published_date')[:4]

        # 📌 Izohlarni olish
        comments = self.object.comments.all().order_by('-created_at')

        context["related_news"] = related_news  # 📌 O'xshash yangiliklar
        context["comments"] = comments  # 📌 Yangilik izohlari
        context["comments_count"] = comments.count()  # 📌 Izohlar soni

        return context

    def post(self, request, *args, **kwargs):
        """ Foydalanuvchi yangi izoh qoldirsa, uni saqlash """
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # AJAX ekanligini tekshirish
            print(request.POST)
            try:
                news = self.get_object()
                full_name = request.POST.get("author")
                phone_number = request.POST.get("phone_number")
                comment_text = request.POST.get("comment")

                if not (full_name and phone_number and comment_text):
                    return JsonResponse({"success": False, "message": "Barcha maydonlarni to‘ldiring!"}, status=400)

                # Yangi izohni saqlash
                Comment.objects.create(news=news, full_name=full_name, phone_number=phone_number, text=comment_text)

                return JsonResponse({"success": True, "message": "Izoh muvaffaqiyatli qo‘shildi!"})
            except Exception as e:
                return JsonResponse({"success": False, "message": f"Xatolik yuz berdi: {str(e)}"}, status=500)
        else:
            return JsonResponse({"success": False, "message": "Faqat AJAX so‘rov qabul qilinadi!"}, status=400)


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