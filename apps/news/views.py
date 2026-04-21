import json
from urllib.parse import urlencode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils.translation import get_language
from django.conf import settings
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from .forms import NewsForm  # Django ModelForm

from apps.members.models import CustomUser

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

    paginate_by = 9

    def get_queryset(self, request):
        news_queryset = News.objects.select_related("author").all().order_by("-published_date")

        search_query = request.GET.get("q", "").strip()
        if search_query:
            search_filter = Q()
            if search_query.isdigit():
                search_filter |= Q(id=int(search_query))
            for code, _name in settings.LANGUAGES:
                search_filter |= Q(**{f"title__{code}__icontains": search_query})
                search_filter |= Q(**{f"content__{code}__icontains": search_query})
            news_queryset = news_queryset.filter(search_filter)

        status_filter = request.GET.get("status", "").strip()
        if status_filter == "published":
            news_queryset = news_queryset.filter(is_published=True)
        elif status_filter == "draft":
            news_queryset = news_queryset.filter(is_published=False)

        return news_queryset

    def get_context_data(self, request):
        news_queryset = self.get_queryset(request)
        paginator = Paginator(news_queryset, self.paginate_by)
        news_list = paginator.get_page(request.GET.get("page"))
        search_query = request.GET.get("q", "").strip()
        status_filter = request.GET.get("status", "").strip()
        all_news = News.objects.all()
        page_query = {
            key: value
            for key, value in {
                "q": search_query,
                "status": status_filter,
            }.items()
            if value
        }

        return {
            "news_list": news_list,
            "search_query": search_query,
            "status_filter": status_filter,
            "page_query": urlencode(page_query),
            "current_path": request.get_full_path(),
            "lang_code": request.COOKIES.get("selected_language", get_language()),
            "LANGUAGES": settings.LANGUAGES,
            "total_count": all_news.count(),
            "published_count": all_news.filter(is_published=True).count(),
            "draft_count": all_news.filter(is_published=False).count(),
            "filtered_count": news_queryset.count(),
            "breadcrumbs": [
                {"title": "Bosh sahifa", "url": reverse('admin-index')},
                {"title": "Yangiliklar", "url": reverse('news-view'), "active": True},
            ],
        }

    def redirect_to_list(self, request):
        return_path = request.POST.get("return_path", "").strip()
        if return_path.startswith("/"):
            return redirect(return_path)
        return redirect("news-view")

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data(request))

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action", "").strip()
        news_id = request.POST.get("news_id", "").strip()

        if not news_id:
            messages.error(request, "Yangilik ID kiritilmadi.")
            return self.redirect_to_list(request)

        news = get_object_or_404(News, id=news_id)

        if action == "open_detail":
            request.session["selected_news_id"] = news.id
            return redirect("news-detail")

        if action == "update_status":
            status = request.POST.get("status", "").strip()
            if status not in {"published", "draft"}:
                messages.error(request, "Status noto'g'ri yuborildi.")
                return self.redirect_to_list(request)

            news.is_published = status == "published"
            news.save(update_fields=["is_published"])
            messages.success(request, "Yangilik holati yangilandi.")
            return self.redirect_to_list(request)

        if action == "delete":
            news.delete()
            messages.success(request, "Yangilik muvaffaqiyatli o'chirildi.")
            return self.redirect_to_list(request)

        messages.error(request, "Noto'g'ri amal yuborildi.")
        return self.redirect_to_list(request)

@method_decorator(login_required, name='dispatch')
class LegacyAddNewsView(View):
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

@method_decorator(login_required, name='dispatch')
class AddNewsView(View):
    template_name = 'news/add_news_view.html'

    def get_form_data(self, request):
        return {
            "title": {code: request.POST.get(f"title_{code}", "").strip() for code, _ in settings.LANGUAGES},
            "content": {code: request.POST.get(f"content_{code}", "").strip() for code, _ in settings.LANGUAGES},
            "is_published": request.POST.get("is_published") == "on",
        }

    def get_context_data(self, request, form_data=None):
        if form_data is None:
            form_data = {
                "title": {},
                "content": {},
                "is_published": False,
            }

        return {
            "lang_code": request.COOKIES.get("selected_language", get_language()),
            "LANGUAGES": settings.LANGUAGES,
            "form_title": form_data["title"],
            "form_content": form_data["content"],
            "form_is_published": form_data["is_published"],
            "breadcrumbs": [
                {"title": "Bosh sahifa", "url": reverse('admin-index')},
                {"title": "Yangiliklar", "url": reverse('news-view')},
                {"title": "Yangilik qo'shish", "url": reverse('add-news-view'), "active": True},
            ],
        }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data(request))

    def post(self, request):
        form_data = self.get_form_data(request)
        image = request.FILES.get('image')

        if not form_data["title"].get('uz'):
            messages.error(request, "O'zbek tilidagi sarlavha majburiy.")
            return render(request, self.template_name, self.get_context_data(request, form_data=form_data))

        if not form_data["content"].get('uz'):
            messages.error(request, "O'zbek tilidagi mazmun majburiy.")
            return render(request, self.template_name, self.get_context_data(request, form_data=form_data))

        News.objects.create(
            title=form_data["title"],
            content=form_data["content"],
            image=image,
            author=request.user,
            is_published=form_data["is_published"],
        )
        messages.success(request, "Yangilik muvaffaqiyatli qo'shildi.")
        return redirect("news-view")

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
class LegacyAnnouncementView(View):
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

@method_decorator(login_required, name='dispatch')
class AnnouncementView(View):
    template_name = 'announcement/announcement-list.html'
    paginate_by = 10

    def get_queryset(self, request):
        announcements = Announcement.objects.select_related("author").all().order_by("-published_date")

        search_query = request.GET.get("q", "").strip()
        if search_query:
            search_filter = Q()
            if search_query.isdigit():
                search_filter |= Q(id=int(search_query))
            for code, _name in settings.LANGUAGES:
                search_filter |= Q(**{f"title__{code}__icontains": search_query})
                search_filter |= Q(**{f"content__{code}__icontains": search_query})
            announcements = announcements.filter(search_filter)

        status_filter = request.GET.get("status", "").strip()
        if status_filter == "published":
            announcements = announcements.filter(is_published=True)
        elif status_filter == "draft":
            announcements = announcements.filter(is_published=False)

        return announcements

    def get_context_data(self, request):
        announcements = self.get_queryset(request)
        paginator = Paginator(announcements, self.paginate_by)
        announcements_page = paginator.get_page(request.GET.get("page"))
        search_query = request.GET.get("q", "").strip()
        status_filter = request.GET.get("status", "").strip()
        page_query = {
            key: value
            for key, value in {
                "q": search_query,
                "status": status_filter,
            }.items()
            if value
        }
        all_announcements = Announcement.objects.all()

        return {
            "announcements": announcements_page,
            "search_query": search_query,
            "status_filter": status_filter,
            "page_query": urlencode(page_query),
            "total_count": all_announcements.count(),
            "published_count": all_announcements.filter(is_published=True).count(),
            "draft_count": all_announcements.filter(is_published=False).count(),
            "filtered_count": announcements.count(),
            "lang_code": request.COOKIES.get("selected_language", get_language()),
            "LANGUAGES": settings.LANGUAGES,
            "breadcrumbs": [
                {"title": "Bosh sahifa", "url": reverse("admin-index")},
                {"title": "E'lonlar", "url": reverse("announcemen-view"), "active": True},
            ],
        }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data(request))

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action", "")
        announcement_id = request.POST.get("announcement_id", "").strip()

        if action == "delete":
            if not announcement_id:
                messages.error(request, "E'lon ID kiritilmadi.")
                return redirect("announcemen-view")

            announcement = get_object_or_404(Announcement, id=announcement_id)
            announcement.delete()
            messages.success(request, "E'lon muvaffaqiyatli o'chirildi.")
            return redirect("announcemen-view")

        if action == "update_status":
            if not announcement_id:
                messages.error(request, "E'lon ID kiritilmadi.")
                return redirect("announcemen-view")

            announcement = get_object_or_404(Announcement, id=announcement_id)
            status = request.POST.get("status")
            if status not in {"published", "draft"}:
                messages.error(request, "Status noto'g'ri yuborildi.")
                return redirect("announcemen-view")

            announcement.is_published = status == "published"
            announcement.save(update_fields=["is_published"])
            messages.success(request, "E'lon holati yangilandi.")
            return redirect("announcemen-view")

        messages.error(request, "Noto'g'ri amal yuborildi.")
        return redirect("announcemen-view")


class LegacyAnnouncementCreateView(LoginRequiredMixin, View):
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


class AnnouncementCreateView(LoginRequiredMixin, View):
    template_name = "announcement/announcement-form.html"

    def get_announcement(self, request):
        pk = self.kwargs.get("pk") or request.GET.get("edit")
        if not pk:
            return None
        return get_object_or_404(Announcement, pk=pk)

    def get_form_data(self, request):
        return {
            "title": {code: request.POST.get(f"title_{code}", "").strip() for code, _ in settings.LANGUAGES},
            "content": {code: request.POST.get(f"content_{code}", "").strip() for code, _ in settings.LANGUAGES},
            "is_published": request.POST.get("is_published") == "on",
        }

    def get_context_data(self, request, form_data=None):
        announcement = self.get_announcement(request)
        is_edit = announcement is not None
        form_action_url = reverse("announcement-create")
        if is_edit:
            form_action_url = f"{form_action_url}?edit={announcement.pk}"

        if form_data is None:
            form_data = {
                "title": announcement.title if announcement else {},
                "content": announcement.content if announcement else {},
                "is_published": announcement.is_published if announcement else False,
            }

        return {
            "announcement": announcement,
            "form_title": form_data["title"],
            "form_content": form_data["content"],
            "form_is_published": form_data["is_published"],
            "LANGUAGES": settings.LANGUAGES,
            "breadcrumbs": [
                {"title": "Bosh sahifa", "url": reverse("admin-index")},
                {"title": "E'lonlar", "url": reverse("announcemen-view")},
                {
                    "title": "E'lonni tahrirlash" if is_edit else "E'lon qo'shish",
                    "url": form_action_url,
                    "active": True,
                },
            ],
            "page_title": "E'lonni tahrirlash" if is_edit else "E'lon qo'shish",
            "page_subtitle": "Mavjud e'lon matnini yangilang." if is_edit else "Yangi e'lon uchun sarlavha va mazmun kiriting.",
            "submit_label": "Yangilash" if is_edit else "Saqlash",
            "form_action_url": form_action_url,
        }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data(request))

    def post(self, request, *args, **kwargs):
        announcement = self.get_announcement(request)
        form_data = self.get_form_data(request)

        if not form_data["title"].get("uz"):
            messages.error(request, "O'zbek tilidagi sarlavha majburiy.")
            return render(request, self.template_name, self.get_context_data(request, form_data=form_data))

        if not form_data["content"].get("uz"):
            messages.error(request, "O'zbek tilidagi mazmun majburiy.")
            return render(request, self.template_name, self.get_context_data(request, form_data=form_data))

        if announcement:
            announcement.title = form_data["title"]
            announcement.content = form_data["content"]
            announcement.is_published = form_data["is_published"]
            announcement.save()
            messages.success(request, "E'lon muvaffaqiyatli yangilandi.")
        else:
            Announcement.objects.create(
                title=form_data["title"],
                content=form_data["content"],
                is_published=form_data["is_published"],
                author=request.user,
            )
            messages.success(request, "E'lon muvaffaqiyatli qo'shildi.")

        return redirect("announcemen-view")
