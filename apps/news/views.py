import json
from django.utils.translation import gettext as _

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.utils.translation import get_language
from django.conf import settings
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .forms import NewsForm  # Django ModelForm

from apps.medical.models import News
from members.models import CustomUser


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
        """ Yangilikni tahrirlash va saqlash """
        news_id = request.session.get("selected_news_id")
        if not news_id:
            return JsonResponse({"error": str(("Yangilik topilmadi!"))}, status=400)

        news = get_object_or_404(News, id=news_id)

        for lang_code, _ in self.LANGUAGES:
            title_field = f"title_{lang_code}"
            content_field = f"content_{lang_code}"
            image_field = f"image_{lang_code}"

            if title_field in request.POST:
                setattr(news, title_field, request.POST[title_field])

            if content_field in request.POST:
                setattr(news, content_field, request.POST[content_field])

            if image_field in request.FILES:
                setattr(news, image_field, request.FILES[image_field])

        news.save()
        return JsonResponse({"status": "success", "message": str(("Yangilik muvaffaqiyatli saqlandi!"))})
