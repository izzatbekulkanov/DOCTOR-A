import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.utils.translation import get_language
from django.conf import settings
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .forms import NewsForm  # Django ModelForm

from apps.medical.models import News, Announcement
from members.models import CustomUser

from django.utils.translation import gettext as _  # 🔹 `gettext` ni import qildik


@method_decorator(login_required, name='dispatch')
class NewsView(View):
    template_name = 'news/news_views.html'

    def get(self, request, *args, **kwargs):
        """ GET so‘rovni qabul qiladi va yangiliklarni chiqaradi """

        # 🔍 Qidiruv so‘rovi
        search_query = request.GET.get("q", "").strip()
        news_queryset = News.objects.all()

        if search_query:
            news_queryset = news_queryset.filter(title__icontains=search_query)

        # 📄 Pagination (Har bir sahifada 5 ta yangilik)
        paginator = Paginator(news_queryset, 5)
        page_number = request.GET.get("page")
        news_list = paginator.get_page(page_number)

        # 🌍 Cookie-dan yoki default tillardan til olish
        lang_code = request.COOKIES.get("selected_language", get_language())

        context = {
            "news_list": news_list,
            "search_query": search_query,
            "lang_code": lang_code,
            "LANGUAGES": settings.LANGUAGES,
        }
        return render(request, self.template_name, context)


class AddNewsView(View):
    template_name = 'news/add_news_view.html'

    def get(self, request, *args, **kwargs):
        """ GET so‘rovni qabul qiladi va formani chiqaradi """
        lang_code = request.COOKIES.get("selected_language", get_language())
        authors = CustomUser.objects.all()  # Barcha mualliflarni olish

        context = {
            "lang_code": lang_code,
            "LANGUAGES": settings.LANGUAGES,
            "authors": authors,  # Mualliflar ro'yxati
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """ Yangilikni bazaga qo‘shish """
        data = request.POST
        title = json.loads(data.get('title', '{}'))
        content = json.loads(data.get('content', '{}'))
        image = request.FILES.get('image')
        is_published = data.get('is_published') == 'on'

        if not title.get('uz'):
            return JsonResponse({"status": "error", "message": _("O‘zbek tilida sarlavha kiritish majburiy!")},
                                status=400)

        news = News.objects.create(
            title=title,
            content=content,
            image=image,
            author=request.user,
            is_published=is_published
        )

        return JsonResponse({"status": "success", "message": _("Yangilik muvaffaqiyatli qo‘shildi!")})



class SetSelectedNewsView(View):
    """ Yangilikni sessionda saqlash """

    def post(self, request, *args, **kwargs):
        news_id = request.POST.get("news_id")
        if not news_id:
            return JsonResponse({"error": "Yangilik ID kelmadi!"}, status=400)

        request.session["selected_news_id"] = news_id  # ✅ Sessionga saqlash
        return JsonResponse({"status": "success"})


class NewsDetailView(View):
    template_name = "news/news_detail.html"

    # 🔹 Tillar ro‘yxati
    LANGUAGES = [
        ("uz", _("O'zbek")),
        ("ru", _("Русский")),
        ("en", _("English")),
        ("de", _("Deutsch")),
        ("tr", _("Türkçe")),
    ]

    def get(self, request, *args, **kwargs):
        """ Yangilikni sessiondan olib ko‘rsatish """
        news_id = request.session.get("selected_news_id")
        if not news_id:
            return JsonResponse({"error": _("Hech qanday yangilik tanlanmagan!")}, status=400)

        news = get_object_or_404(News, id=news_id)

        context = {
            "news": news,
            "LANGUAGES": self.LANGUAGES  # 🔹 Tillar ro‘yxati shablonga yuboriladi
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        print("🔹 POST so‘rovi qabul qilindi!")  # ✅ Debug
        print(f"📩 Yuborilgan ma'lumotlar: {request.POST}")  # ✅ Debug

        # 🔹 Yangilik ID olish
        news_id = request.POST.get("news_id")
        if not news_id:
            print("❌ Yangilik ID kelmadi!")  # ❌ Debug
            return JsonResponse({"error": "Yangilik ID kelmadi!"}, status=400)

        # 🔹 Yangilikni bazadan olish
        news = get_object_or_404(News, id=news_id)
        print(f"📰 Yangilik bazadan topildi: {news}")  # ✅ Debug

        # ✅ **Ko‘p tilli yangilash**
        for lang_code, _ in self.LANGUAGES:
            title_value = request.POST.get(f"title_{lang_code}", "").strip()
            content_value = request.POST.get(f"content_{lang_code}", "").strip()

            if title_value:
                news.title[lang_code] = title_value  # JSONField uchun
            if content_value:
                news.content[lang_code] = content_value  # JSONField uchun

        # ✅ **Rasmni yangilash**
        if "image" in request.FILES:
            news.image = request.FILES["image"]

        # 🔹 Yangilikni saqlash
        news.save()
        print("✅ Yangilik muvaffaqiyatli yangilandi!")  # ✅ Debug

        return JsonResponse({"status": "success", "message": "Yangilik barcha tillarda yangilandi."})

class NewsDeleteView(View):
    def post(self, request, *args, **kwargs):
        news_id = request.POST.get("news_id")
        if not news_id:
            return JsonResponse({"error": "Yangilik ID kelmadi!"}, status=400)

        news = get_object_or_404(News, id=news_id)
        news.delete()

        return JsonResponse({"status": "success", "message": "Yangilik muvaffaqiyatli o‘chirildi!"})



@method_decorator(login_required, name='dispatch')
class AnnouncementView(View):
    template_name = 'announcement/announcement-list.html'

    def get(self, request, *args, **kwargs):
        announcements = Announcement.objects.filter(is_published=True)  # 🔹 Chop etilgan e'lonlar
        # 🌍 Cookie-dan yoki default tillardan til olish
        lang_code = request.COOKIES.get("selected_language", get_language())

        context = {
            "announcements": announcements,
            "lang_code": lang_code,
            "LANGUAGES": settings.LANGUAGES,
        }
        return render(request, self.template_name, context)


class AnnouncementCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        """ AJAX orqali yangi e'lon yaratish """
        title_uz = request.POST.get("title_uz")
        title_ru = request.POST.get("title_ru")
        title_en = request.POST.get("title_en")
        title_de = request.POST.get("title_de")
        title_tr = request.POST.get("title_tr")

        content_uz = request.POST.get("content_uz")
        content_ru = request.POST.get("content_ru")
        content_en = request.POST.get("content_en")
        content_de = request.POST.get("content_de")
        content_tr = request.POST.get("content_tr")

        is_published = request.POST.get("is_published") == "on"

        if not title_uz or not content_uz:
            return JsonResponse({"error": _("O‘zbek tilidagi sarlavha va mazmun talab qilinadi!")}, status=400)

        announcement = Announcement.objects.create(
            title={"uz": title_uz, "ru": title_ru, "en": title_en, "de": title_de, "tr": title_tr},
            content={"uz": content_uz, "ru": content_ru, "en": content_en, "de": content_de, "tr": content_tr},
            is_published=is_published,
            author=request.user
        )

        return JsonResponse({
            "status": "success",
            "message": _("E'lon muvaffaqiyatli yaratildi!"),
            "announcement": {
                "id": announcement.id,
                "title": announcement.title.get("uz", ""),
                "content": announcement.content.get("uz", ""),
                "published_date": announcement.published_date.strftime("%Y-%m-%d %H:%M"),
                "views_count": announcement.views_count
            }
        })
