import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils.translation import get_language
from django.conf import settings
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from .forms import NewsForm  # Django ModelForm

from members.models import CustomUser

from django.utils.translation import gettext as _  # 🔹 `gettext` ni import qildik

from .models import News, Announcement


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

        # 📄 Pagination (Har bir sahifada 6 ta yangilik)
        paginator = Paginator(news_queryset, 6)
        page_number = request.GET.get("page")
        news_list = paginator.get_page(page_number)

        # 🌍 Cookie-dan yoki default tillardan til olish
        lang_code = request.COOKIES.get("selected_language", get_language())

        # Breadcrumb uchun kontekst
        breadcrumbs = [
            {"title": "Bosh sahifa", "url": "{% url 'admin-index' %}"},
            {"title": "Yangiliklar", "url": "{% url 'news-view' %}", "active": True},
        ]

        breadcrumbs = [
            {"title": "Bosh sahifa", "url": reverse('admin-index')},
            {"title": "Foydalanuvchilar", "url": reverse('news-view'), "active": True},
        ]

        context = {
            "news_list": news_list,
            "search_query": search_query,
            "lang_code": lang_code,
            "LANGUAGES": settings.LANGUAGES,
            "breadcrumbs": breadcrumbs,  # Breadcrumb qo‘shildi
        }
        return render(request, self.template_name, context)

@method_decorator(login_required, name='dispatch')
class AddNewsView(View):
    template_name = 'news/add_news_view.html'

    def get(self, request, *args, **kwargs):
        """ GET so‘rovni qabul qiladi va formani chiqaradi """
        lang_code = request.COOKIES.get("selected_language", get_language())
        authors = CustomUser.objects.all()  # Barcha mualliflarni olish

        # Breadcrumb uchun kontekst
        breadcrumbs = [
            {"title": "Bosh sahifa", "url": reverse('admin-index')},
            {"title": "Yangiliklar", "url": reverse('news-view')},
            {"title": "Yangilik qo‘shish", "url": reverse('add-news-view'), "active": True},
        ]

        context = {
            "lang_code": lang_code,
            "LANGUAGES": settings.LANGUAGES,
            "authors": authors,  # Mualliflar ro'yxati
            "breadcrumbs": breadcrumbs,  # Breadcrumb qo‘shildi
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """ Yangilikni bazaga qo‘shish """
        data = request.POST
        title = json.loads(data.get('title', '{}'))
        content = json.loads(data.get('content', '{}'))
        image = request.FILES.get('image')
        is_published = data.get('is_published') == 'on'
        print(data.get('is_published'))

        if not title.get('uz'):
            return JsonResponse({"status": "error", "message": _("O‘zbek tilida sarlavha kiritish majburiy!")},
                                status=400)

        news = News.objects.create(
            title=title,
            content=content,
            image=image,
            author=request.user,
            is_published=True
        )

        return JsonResponse({"status": "success", "message": _("Yangilik muvaffaqiyatli qo‘shildi!")})

@csrf_exempt
def toggle_news_status(request, news_id):
    """ Yangilikning is_published statusini o'zgartirish """
    if request.method == "POST":
        news = get_object_or_404(News, id=news_id)
        news.is_published = not news.is_published  # Holatni teskarisiga o'zgartirish
        news.save()
        return JsonResponse({"is_published": news.is_published})
    return JsonResponse({"error": "Noto‘g‘ri so‘rov"}, status=400)


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

        # Breadcrumb uchun kontekst
        breadcrumbs = [
            {"title": "Bosh sahifa", "url": reverse('admin-index')},
            {"title": "Yangiliklar", "url": reverse('news-view')},
            {"title": "Yangilik tahrirlash", "url": reverse('news-detail'), "active": True},
        ]


        context = {
            "news": news,
            "LANGUAGES": self.LANGUAGES,  # 🔹 Tillar ro‘yxati shablonga yuboriladi
            "breadcrumbs": breadcrumbs,  # Breadcrumb qo‘shildi
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
            title_key = f"title_{lang_code}"
            content_key = f"content_{lang_code}"

            if title_key in request.POST:
                news.title[lang_code] = request.POST.get(title_key, "").strip()

            if content_key in request.POST:
                news.content[lang_code] = request.POST.get(content_key, "").strip()

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
