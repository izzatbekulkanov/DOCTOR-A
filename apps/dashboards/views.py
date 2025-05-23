from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count
from django.http import JsonResponse
from django.views.generic import TemplateView, DetailView
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext as _
from django.db.models import Q
from django.db import models
from django.views.generic import ListView
from django.utils.translation import get_language
from apps.medical.models import Video, ClinicEquipment
from apps.news.models import News, Comment, Announcement
from members.models import CustomUser


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

    def get_object(self, queryset=None):
        """ Yangilikni olish va ko‘rishlar sonini oshirish """
        obj = super().get_object(queryset)
        obj.views_count = models.F('views_count') + 1  # Ko‘rishlar sonini oshirish
        obj.save(update_fields=['views_count'])  # Faqat views_count ni saqlash
        obj.refresh_from_db()  # Yangilangan qiymatni olish
        return obj

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
        context["views_count"] = self.object.views_count  # 📌 Yangilik ko‘rilishlar soni

        return context

    def post(self, request, *args, **kwargs):
        """ Foydalanuvchi yangi izoh qoldirsa, uni saqlash """
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # AJAX ekanligini tekshirish
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
        """ E'lonlar ro'yxatini pagination va qidirish bilan olish """
        context = super().get_context_data(**kwargs)

        # Qidirish so'rovini olish
        search_query = self.request.GET.get("q", "").strip()

        # Faqat chop etilgan e'lonlarni olish
        announcements = Announcement.objects.filter(is_published=True)

        # Qidirishni qo'llash (JSONField ichidagi ma'lumotni qidirish)
        if search_query:
            announcements = announcements.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )

        # Pagination
        page_number = self.request.GET.get("page", 1)
        paginator = Paginator(announcements, 10)  # Har bir sahifada 10 ta e'lon
        page_obj = paginator.get_page(page_number)

        context["announcements"] = page_obj  # Sahifalangan e'lonlar
        context["search_query"] = search_query  # Qidiruv so'rovi

        return context


class AnnouncementDetailView(DetailView):
    model = Announcement
    template_name = "views/announcement-detail-dashboard.html"
    context_object_name = "announcement"

    def get_object(self, queryset=None):
        """ E'lonni topish va ko'rishlar sonini oshirish """
        obj = super().get_object(queryset)
        obj.increment_views()  # Ko'rishlar sonini oshirish
        return obj

    def get_context_data(self, **kwargs):
        """ Kontekstga qo'shimcha ma'lumotlar qo'shish """
        context = super().get_context_data(**kwargs)
        context["related_announcements"] = Announcement.objects.filter(
            is_published=True
        ).exclude(id=self.object.id).order_by('-published_date')[:4]  # O'xshash e'lonlar
        return context


class EmployeeView(TemplateView):
    template_name = "views/employee-dashboard.html"

    def get_context_data(self, **kwargs):
        """ Xodimlar ro'yxati uchun qidirish va pagination qo'shish """
        context = super().get_context_data(**kwargs)

        # 🔍 Qidiruv so‘rovini olish
        search_query = self.request.GET.get('q', '').strip()

        # 📌 Faqat faol xodimlarni olish
        employees = CustomUser.objects.filter(is_active_employee=True, is_superuser=False)

        # ✅ Qidiruv: ism, telefon raqam yoki lavozim bo‘yicha
        if search_query:
            employees = employees.filter(
                Q(full_name__icontains=search_query) |
                Q(phone_number__icontains=search_query) |
                Q(job_title__icontains=search_query)
            )

        # 📌 8 tadan sahifalash
        paginator = Paginator(employees, 8)
        page_number = self.request.GET.get('page')
        employees_page = paginator.get_page(page_number)

        # 📌 Kontekstga ma’lumotlarni qo‘shish
        context["employees"] = employees_page
        context["search_query"] = search_query
        return context

class EmployeeDetailView(DetailView):
    model = CustomUser
    template_name = "views/employee-detail-dashboard.html"
    context_object_name = "employee"

    def get_queryset(self):
        # Faqat faol xodimlarni ko'rsatish
        return CustomUser.objects.filter(is_active_employee=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Xodimning faoliyat tarixini qo'shish
        context['activity_history'] = self.object.activity_history.all()
        # Sayt sozlamalari (masalan, telefon raqami uchun)

        return context

class VideosView(TemplateView):
    template_name = "views/videos-dashboard.html"
    redirect_field_name = 'redirect_to'

    def get_context_data(self, **kwargs):
        """ Asosiy sahifa uchun barcha ma'lumotlarni olish """
        context = super().get_context_data(**kwargs)

        # Qidiruv so‘rovi
        search_query = self.request.GET.get('q', '').strip()

        # Videolarni olish
        videos = Video.objects.filter(is_active=True)

        # Qidiruv filtri (sarlavha bo‘yicha)
        if search_query:
            videos = videos.filter(
                Q(title__contains=search_query)  # JSONField'da qidiruv
            )

        # Tartiblash (eng yangi avval)
        videos = videos.order_by('-created_at')

        # Paginatsiya (har sahifada 6 ta video)
        paginator = Paginator(videos, 6)
        page_number = self.request.GET.get('page')
        try:
            videos_page = paginator.page(page_number)
        except PageNotAnInteger:
            videos_page = paginator.page(1)
        except EmptyPage:
            videos_page = paginator.page(paginator.num_pages)

        context.update({
            'videos': videos_page,
            'search_query': search_query,
        })
        return context


class ClinicEquipmentListView(ListView):
    model = ClinicEquipment
    template_name = 'views/equipment_list.html'
    context_object_name = 'equipments'
    paginate_by = 6

    def get_queryset(self):
        queryset = ClinicEquipment.objects.filter(is_active=True).order_by('-created_at')
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['language_code'] = get_language()
        return context

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        paginator = Paginator(self.object_list, self.paginate_by)
        page = request.GET.get('page', 1)

        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page
            page_obj = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page of results
            page_obj = paginator.page(paginator.num_pages)

        context = self.get_context_data(page_obj=page_obj)
        return self.render_to_response(context)
class EquipmentDetailView(DetailView):
    model = ClinicEquipment
    template_name = 'views/equipment_detail.html'
    context_object_name = 'equipment'

    def get_queryset(self):
        # Faqat faol qurilmalarni ko'rsatish
        return ClinicEquipment.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        language_code = get_language()
        context['language_code'] = language_code


        return context