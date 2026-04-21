import json
from datetime import datetime, timedelta
import traceback
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, DetailView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from PIL import Image
from django.urls import reverse
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
from urllib.parse import urlencode, urlparse
from django.utils.html import strip_tags
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from config import settings
from config.settings import LANGUAGES
from config.telegram_bot import send_message
from apps.logs.models import Log
from apps.members.models import CustomUser, Appointment, EmployeeActivityHistory
from apps.news.models import News, Announcement, Comment
from .forms import VideoForm
from .models import SiteSettings, MainPageBanner, DoctorAInfo, ContactPhone, Partner, MedicalCheckupApplication, \
    ClinicEquipment, Video, ClinicService, FLATICON_ICON_CHOICES


class MainView(TemplateView):
    template_name = 'views/main.html'

    @staticmethod
    def get_ratio(value, total):
        if not total:
            return 0
        return int(round((value / total) * 100))

    @staticmethod
    def get_user_display(user):
        if not user:
            return "-"
        return user.full_name or user.get_full_name() or user.username

    @staticmethod
    def get_badge_classes(is_ok):
        return (
            "badge bg-success-subtle text-success",
            "bg-success-subtle text-success",
        ) if is_ok else (
            "badge bg-warning-subtle text-warning",
            "bg-warning-subtle text-warning",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.localtime()
        month_ago = now - timedelta(days=30)
        week_ago = now - timedelta(days=7)

        site_settings = SiteSettings.objects.first()
        banner = MainPageBanner.objects.first()

        users = CustomUser.objects.all()
        employees = users.filter(is_active_employee=True)
        appointments = Appointment.objects.select_related("employee")
        activities = EmployeeActivityHistory.objects.select_related("user")
        checkups = MedicalCheckupApplication.objects.all()
        news_items = News.objects.select_related("author")
        announcements = Announcement.objects.select_related("author")
        comments = Comment.objects.select_related("news")
        partners = Partner.objects.all()
        equipments = ClinicEquipment.objects.all()
        videos = Video.objects.all()
        logs = Log.objects.select_related("user")

        total_users = users.count()
        active_users = users.filter(is_active=True).count()
        staff_users = users.filter(is_staff=True).count()
        total_roles = Group.objects.count()

        total_employees = employees.count()
        active_employees = employees.filter(is_active=True).count()
        employees_with_activity = employees.filter(activity_history__isnull=False).distinct().count()
        total_activities = activities.count()

        total_appointments = appointments.count()
        pending_appointments = appointments.filter(status="pending").count()
        approved_appointments = appointments.filter(status="approved").count()
        canceled_appointments = appointments.filter(status="canceled").count()
        monthly_appointments = appointments.filter(created_at__gte=month_ago).count()

        total_checkups = checkups.count()
        unseen_checkups = checkups.filter(is_seen=False).count()
        monthly_checkups = checkups.filter(created_at__gte=month_ago).count()

        total_news = news_items.count()
        published_news = news_items.filter(is_published=True).count()
        draft_news = total_news - published_news
        monthly_news = news_items.filter(created_at__gte=month_ago).count()
        total_news_views = news_items.aggregate(total=Sum("views_count"))["total"] or 0

        total_announcements = announcements.count()
        published_announcements = announcements.filter(is_published=True).count()
        draft_announcements = total_announcements - published_announcements
        monthly_announcements = announcements.filter(published_date__gte=month_ago).count()
        total_announcement_views = announcements.aggregate(total=Sum("views_count"))["total"] or 0

        total_partners = partners.count()
        active_partners = partners.filter(is_active=True).count()

        total_equipments = equipments.count()
        active_equipments = equipments.filter(is_active=True).count()

        total_videos = videos.count()
        active_videos = videos.filter(is_active=True).count()

        total_comments = comments.count()
        total_logs = logs.count()
        weekly_error_logs = logs.filter(timestamp__gte=week_ago, status_code__gte=400).count()

        total_content = total_news + total_announcements
        published_content = published_news + published_announcements
        total_content_views = total_news_views + total_announcement_views
        pending_requests = pending_appointments + unseen_checkups

        social_fields = ("facebook_url", "telegram_url", "instagram_url", "youtube_url")
        configured_social_links = sum(1 for field in social_fields if site_settings and getattr(site_settings, field))
        media_assets_total = 5
        configured_media_assets = sum(
            1 for field in ("logo_dark", "logo_light", "video1", "video2")
            if site_settings and getattr(site_settings, field)
        ) + (1 if banner else 0)
        settings_fields_total = 9
        configured_settings_fields = sum(
            1
            for value in (
                site_settings.site_name if site_settings else "",
                site_settings.contact_email if site_settings else "",
                site_settings.contact_phone if site_settings else "",
                site_settings.address if site_settings else "",
                site_settings.working_hours if site_settings else "",
                site_settings.logo_dark if site_settings else None,
                site_settings.logo_light if site_settings else None,
                site_settings.video1 if site_settings else None,
                site_settings.video2 if site_settings else None,
            )
            if value
        )

        content_publish_ratio = self.get_ratio(published_content, total_content)
        media_assets_ratio = self.get_ratio(configured_media_assets, media_assets_total)
        settings_completion_ratio = self.get_ratio(configured_settings_fields, settings_fields_total)
        active_user_ratio = self.get_ratio(active_users, total_users)
        activity_coverage_ratio = self.get_ratio(employees_with_activity, total_employees)

        hero_metrics = [
            {
                "title": _("Faol foydalanuvchilar"),
                "value": active_users,
                "subtitle": _("Jami %(count)s ta foydalanuvchidan") % {"count": total_users},
                "icon": "ri-user-star-line",
                "accent": "primary",
            },
            {
                "title": _("Kutilayotgan so'rovlar"),
                "value": pending_requests,
                "subtitle": _("Qabul %(appointments)s ta, ko'rik %(checkups)s ta") % {
                    "appointments": pending_appointments,
                    "checkups": unseen_checkups,
                },
                "icon": "ri-notification-3-line",
                "accent": "warning",
            },
            {
                "title": _("Chop etilgan kontent"),
                "value": published_content,
                "subtitle": _("Jami %(count)s ta materialdan") % {"count": total_content},
                "icon": "ri-article-line",
                "accent": "success",
            },
            {
                "title": _("7 kunlik xato loglari"),
                "value": weekly_error_logs,
                "subtitle": _("Jami %(count)s ta logdan") % {"count": total_logs},
                "icon": "ri-pulse-line",
                "accent": "danger",
            },
        ]

        module_cards = [
            {
                "title": _("Foydalanuvchilar"),
                "value": total_users,
                "subtitle": _("Faol %(active)s ta, admin %(staff)s ta") % {
                    "active": active_users,
                    "staff": staff_users,
                },
                "meta": _("Rollar: %(count)s") % {"count": total_roles},
                "icon": "ri-group-line",
                "accent": "primary",
                "url": reverse("users-view"),
            },
            {
                "title": _("Xodimlar"),
                "value": total_employees,
                "subtitle": _("Faoliyat tarixi %(count)s ta yozuv") % {"count": total_activities},
                "meta": _("Faoliyatli xodimlar: %(count)s") % {"count": employees_with_activity},
                "icon": "ri-stethoscope-line",
                "accent": "info",
                "url": reverse("employee-list"),
            },
            {
                "title": _("Qabullar"),
                "value": total_appointments,
                "subtitle": _("Kutilmoqda %(pending)s ta") % {"pending": pending_appointments},
                "meta": _("30 kunda %(count)s ta murojaat") % {"count": monthly_appointments},
                "icon": "ri-calendar-check-line",
                "accent": "warning",
                "url": reverse("appointment-view"),
            },
            {
                "title": _("Ko'rik arizalari"),
                "value": total_checkups,
                "subtitle": _("Ko'rilmagan %(count)s ta") % {"count": unseen_checkups},
                "meta": _("30 kunda %(count)s ta ariza") % {"count": monthly_checkups},
                "icon": "ri-file-list-3-line",
                "accent": "danger",
                "url": reverse("medical-checkup-applications"),
            },
            {
                "title": _("Yangiliklar"),
                "value": total_news,
                "subtitle": _("Chop etilgan %(published)s ta") % {"published": published_news},
                "meta": _("Ko'rishlar: %(count)s") % {"count": total_news_views},
                "icon": "ri-newspaper-line",
                "accent": "success",
                "url": reverse("news-view"),
            },
            {
                "title": _("E'lonlar"),
                "value": total_announcements,
                "subtitle": _("Chop etilgan %(published)s ta") % {"published": published_announcements},
                "meta": _("Ko'rishlar: %(count)s") % {"count": total_announcement_views},
                "icon": "ri-megaphone-line",
                "accent": "secondary",
                "url": reverse("announcemen-view"),
            },
            {
                "title": _("Hamkorlar va media"),
                "value": total_partners,
                "subtitle": _("Faol hamkorlar %(count)s ta") % {"count": active_partners},
                "meta": _("Videolar: %(videos)s ta, faol %(active)s ta") % {
                    "videos": total_videos,
                    "active": active_videos,
                },
                "icon": "ri-handshake-line",
                "accent": "primary",
                "url": reverse("partners-info"),
            },
            {
                "title": _("Jihozlar"),
                "value": total_equipments,
                "subtitle": _("Faol jihozlar %(count)s ta") % {"count": active_equipments},
                "meta": _("Izohlar: %(count)s ta") % {"count": total_comments},
                "icon": "ri-hospital-line",
                "accent": "dark",
                "url": reverse("clinic-equipment"),
            },
        ]

        readiness_metrics = [
            {
                "title": _("Sozlamalar to'liqligi"),
                "value": settings_completion_ratio,
                "description": _("Kontakt, manzil va media maydonlari qamrovi"),
                "progress": settings_completion_ratio,
                "accent": "primary",
            },
            {
                "title": _("Kontent nashri"),
                "value": content_publish_ratio,
                "description": _("Yangilik va e'lonlarning chop etilgan ulushi"),
                "progress": content_publish_ratio,
                "accent": "success",
            },
            {
                "title": _("Media aktivlar"),
                "value": media_assets_ratio,
                "description": _("Logo, video va banner fayllari tayyorligi"),
                "progress": media_assets_ratio,
                "accent": "info",
            },
            {
                "title": _("Xodim faoliyati qamrovi"),
                "value": activity_coverage_ratio,
                "description": _("Faoliyat yozuvi mavjud xodimlar ulushi"),
                "progress": activity_coverage_ratio,
                "accent": "warning",
            },
            {
                "title": _("Faol foydalanuvchilar"),
                "value": active_user_ratio,
                "description": _("Tizimda faol holatdagi akkauntlar ulushi"),
                "progress": active_user_ratio,
                "accent": "secondary",
            },
        ]

        settings_badge, settings_surface = self.get_badge_classes(bool(site_settings))
        banner_badge, banner_surface = self.get_badge_classes(bool(banner))
        video_badge, video_surface = self.get_badge_classes(configured_media_assets >= 3)
        social_badge, social_surface = self.get_badge_classes(configured_social_links >= 2)
        monitoring_badge, monitoring_surface = self.get_badge_classes(weekly_error_logs == 0)

        system_checks = [
            {
                "title": _("Sayt sozlamalari"),
                "value": _("Tayyor") if site_settings else _("Yo'q"),
                "detail": site_settings.site_name if site_settings and site_settings.site_name else _("Asosiy ma'lumotlar to'liq kiritilmagan"),
                "badge_class": settings_badge,
                "surface_class": settings_surface,
                "icon": "ri-settings-3-line",
            },
            {
                "title": _("Asosiy banner"),
                "value": _("Mavjud") if banner else _("Yo'q"),
                "detail": _("Landing sahifasi banneri %(state)s") % {
                    "state": _("biriktirilgan") if banner else _("hali yuklanmagan")
                },
                "badge_class": banner_badge,
                "surface_class": banner_surface,
                "icon": "ri-image-2-line",
            },
            {
                "title": _("Video blok"),
                "value": _("%(count)s/4 fayl") % {"count": configured_media_assets - (1 if banner else 0)},
                "detail": _("Logo va video fayllarining joriy holati"),
                "badge_class": video_badge,
                "surface_class": video_surface,
                "icon": "ri-video-line",
            },
            {
                "title": _("Ijtimoiy tarmoqlar"),
                "value": _("%(count)s/4 havola") % {"count": configured_social_links},
                "detail": _("Facebook, Telegram, Instagram va YouTube holati"),
                "badge_class": social_badge,
                "surface_class": social_surface,
                "icon": "ri-share-forward-line",
            },
            {
                "title": _("Monitoring"),
                "value": _("Barqaror") if weekly_error_logs == 0 else _("E'tibor kerak"),
                "detail": _("So'nggi 7 kunda %(count)s ta xatolik logi") % {"count": weekly_error_logs},
                "badge_class": monitoring_badge,
                "surface_class": monitoring_surface,
                "icon": "ri-pulse-line",
            },
        ]

        quick_links = [
            {
                "title": _("Sozlamalar"),
                "description": _("Asosiy sayt ma'lumotlari va media fayllari"),
                "url": reverse("admin-setting-index"),
                "icon": "ri-settings-3-line",
            },
            {
                "title": _("Foydalanuvchilar"),
                "description": _("Admin, staff va klinika xodimlari boshqaruvi"),
                "url": reverse("users-view"),
                "icon": "ri-group-line",
            },
            {
                "title": _("Yangiliklar"),
                "description": _("Kontent va ko'rishlar oqimini boshqarish"),
                "url": reverse("news-view"),
                "icon": "ri-newspaper-line",
            },
            {
                "title": _("Qabullar"),
                "description": _("Murojaatlar va statuslarni kuzatish"),
                "url": reverse("appointment-view"),
                "icon": "ri-calendar-check-line",
            },
            {
                "title": _("Jihozlar"),
                "description": _("Klinika uskunalari va media ma'lumotlari"),
                "url": reverse("clinic-equipment"),
                "icon": "ri-hospital-line",
            },
            {
                "title": _("Bot"),
                "description": _("Telegram bot sozlamalari va jo'natish holati"),
                "url": reverse("bot-control"),
                "icon": "ri-robot-2-line",
            },
            {
                "title": _("Videolar"),
                "description": _("Landing uchun video kontentni yangilash"),
                "url": reverse("video-list"),
                "icon": "ri-video-line",
            },
        ]

        context.update(
            {
                "site_settings": site_settings,
                "banner": banner,
                "dashboard_now": now,
                "breadcrumbs": [
                    {"title": _("Bosh sahifa"), "url": reverse("admin-index")},
                    {"title": _("Dashboard"), "url": reverse("admin-index"), "active": True},
                ],
                "dashboard_site_name": site_settings.site_name if site_settings and site_settings.site_name else "Doctor-A",
                "hero_metrics": hero_metrics,
                "module_cards": module_cards,
                "readiness_metrics": readiness_metrics,
                "system_checks": system_checks,
                "quick_links": quick_links,
                "recent_appointments": appointments.order_by("-created_at")[:5],
                "recent_checkups": checkups.order_by("-created_at")[:5],
                "recent_users": users.order_by("-date_joined")[:5],
                "recent_activities": activities.order_by("-created_at")[:5],
                "top_news": news_items.order_by("-views_count", "-published_date")[:4],
                "top_announcements": announcements.order_by("-views_count", "-published_date")[:4],
                "recent_logs": logs.order_by("-timestamp")[:6],
                "pending_appointments": pending_appointments,
                "approved_appointments": approved_appointments,
                "canceled_appointments": canceled_appointments,
                "unseen_checkups": unseen_checkups,
                "published_news": published_news,
                "draft_news": draft_news,
                "published_announcements": published_announcements,
                "draft_announcements": draft_announcements,
                "monthly_news": monthly_news,
                "monthly_announcements": monthly_announcements,
                "total_content_views": total_content_views,
                "total_comments": total_comments,
                "total_logs": total_logs,
                "monthly_appointments": monthly_appointments,
                "monthly_checkups": monthly_checkups,
                "main_user_name": self.get_user_display(self.request.user),
            }
        )
        return context

@method_decorator(login_required, name='dispatch')
class MainSettingsView(TemplateView):
    template_name = 'views/main-settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.objects.first()
        context['banner'] = MainPageBanner.objects.first()
        context['LANGUAGES'] = settings.LANGUAGES
        return context

    @staticmethod
    def normalize_rich_text(value):
        normalized = (value or "").strip()
        plain_text = strip_tags(normalized).replace("\xa0", " ").strip()
        if not plain_text:
            return ""
        return normalized

    @staticmethod
    def normalize_uzbek_phone(value):
        digits = "".join(ch for ch in (value or "") if ch.isdigit())
        if digits.startswith("998"):
            digits = digits[3:]
        digits = digits[:9]

        if not digits:
            return ""

        groups = [
            digits[:2],
            digits[2:5],
            digits[5:7],
            digits[7:9],
        ]
        return "+998 " + " ".join(group for group in groups if group)

    def post(self, request, *args, **kwargs):
        # SiteSettings uchun
        site_settings = SiteSettings.objects.first() or SiteSettings()

        site_settings.site_name = request.POST.get('site_name', "").strip()
        site_settings.contact_email = request.POST.get('contact_email', "").strip()
        site_settings.contact_phone = self.normalize_uzbek_phone(request.POST.get('contact_phone', ""))
        site_settings.address = self.normalize_rich_text(request.POST.get('address', ""))
        site_settings.maintenance_mode = request.POST.get('maintenance_mode') == 'on'
        site_settings.working_hours = self.normalize_rich_text(request.POST.get('working_hours', ""))
        site_settings.facebook_url = request.POST.get('facebook_url', "").strip()
        site_settings.telegram_url = request.POST.get('telegram_url', "").strip()
        site_settings.instagram_url = request.POST.get('instagram_url', "").strip()
        site_settings.youtube_url = request.POST.get('youtube_url', "").strip()

        # Logotiplar
        if 'logo_dark' in request.FILES:
            # Logo faylini original o'lcham va sifatini saqlagan holda yozamiz.
            site_settings.logo_dark = request.FILES['logo_dark']
        if 'logo_light' in request.FILES:
            # Logo faylini original o'lcham va sifatini saqlagan holda yozamiz.
            site_settings.logo_light = request.FILES['logo_light']

        # 🔹 Video fayllarni saqlash
        if 'video1' in request.FILES:
            site_settings.video1 = request.FILES['video1']
        if 'video2' in request.FILES:
            site_settings.video2 = request.FILES['video2']

        site_settings.save()

        # Banner uchun
        image = request.FILES.get('banner_image')
        description = {
            code: self.normalize_rich_text(request.POST.get(f'description_{code}', ""))
            for code, name in settings.LANGUAGES
        }

        missing_fields = []
        if not description.get('uz'):
            missing_fields.append("O'zbek tili uchun tavsif majburiy.")

        if missing_fields:
            messages.error(request, " ".join(missing_fields))
            context = self.get_context_data()
            return render(request, self.template_name, context)

        banner = MainPageBanner.objects.first()

        if not banner and not image:
            messages.error(request, "Banner rasmi majburiy.")
            context = self.get_context_data()
            return render(request, self.template_name, context)

        if banner:
            banner.description = description
            if image:
                banner.image = image
            banner.save()
        else:
            banner = MainPageBanner(image=image if image else None, description=description)
            banner.save()

        messages.success(request, "Sayt sozlamalari, videolar va banner muvaffaqiyatli saqlandi!")
        return redirect('admin-setting-index')


class MainPageBannerView(TemplateView):
    template_name = 'views/main-page-banner.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['banner'] = MainPageBanner.objects.first()  # Faqat eng birinchi bannerni olish
        context['LANGUAGES'] = LANGUAGES
        return context

    def post(self, request, *args, **kwargs):
        """ Bannerni faqat bitta nusxada saqlash va mavjud bo‘lsa yangilash """

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # AJAX so‘rovi tekshiriladi
            image = request.FILES.get('banner_image')  # Yangi yuklangan rasm
            description = {code: request.POST.get(f'description[{code}]', "").strip() for code, name in LANGUAGES}

            print(f"🟢 So‘rov qabul qilindi! image={'bor' if image else 'yo‘q'}")

            # **Xatoliklarni tekshirish**
            missing_fields = []

            if not description.get('uz'):
                missing_fields.append("📌 O'zbek tili uchun tavsif majburiy.")

            for code, name in LANGUAGES:
                if not description[code]:
                    missing_fields.append(f"📌 {name} tili uchun tavsif kiritilmagan.")

            if missing_fields:
                print("❌ Xatoliklar ro‘yxati:", missing_fields)
                return JsonResponse({"success": False, "error": "<br>".join(missing_fields)}, status=400)

            # **Bazada mavjud banner bor yoki yo‘qligini tekshiramiz**
            banner = MainPageBanner.objects.first()  # Faqat eng birinchi banner

            if banner:  # **Agar mavjud bo‘lsa, uni yangilaymiz**
                print(f"✏️ Mavjud banner yangilanmoqda... ID: {banner.id}")
                banner.description = description
                if image:  # **Agar yangi rasm bo‘lsa, uni almashtiramiz**
                    print("📸 Yangi rasm yuklandi, almashtirildi.")
                    banner.image = image
                banner.save()
                print("✅ Banner muvaffaqiyatli yangilandi!")
                return JsonResponse({"success": True, "message": "✅ Banner muvaffaqiyatli yangilandi!"})
            else:  # **Agar banner mavjud bo‘lmasa, yangisini qo‘shamiz**
                print("🆕 Yangi banner qo‘shilmoqda...")
                banner = MainPageBanner(image=image, description=description)
                banner.save()
                print(f"✅ Yangi banner qo‘shildi! ID: {banner.id}")
                return JsonResponse({"success": True, "message": "✅ Banner muvaffaqiyatli qo‘shildi!"})

        print("❌ Noto‘g‘ri so‘rov keldi!")
        return JsonResponse({"success": False, "error": "❌ Noto‘g‘ri so‘rov!"}, status=400)


def get_banner(request, banner_id):
    """ AJAX orqali bitta banner ma'lumotlarini qaytarish """
    try:
        banner = MainPageBanner.objects.get(id=banner_id)
        return JsonResponse({
            "success": True,
            "banner_id": banner.id,
            "image_url": banner.image.url,
            "description": banner.description
        })
    except MainPageBanner.DoesNotExist:
        return JsonResponse({"success": False, "error": "❌ Bunday banner topilmadi!"}, status=404)


def delete_banner(request, banner_id):
    """ AJAX orqali bannerni o‘chirish """
    if request.method == "DELETE":
        try:
            banner = MainPageBanner.objects.get(id=banner_id)
            banner.delete()
            return JsonResponse({"success": True, "message": "✅ Banner muvaffaqiyatli o‘chirildi!"})
        except MainPageBanner.DoesNotExist:
            return JsonResponse({"success": False, "error": "❌ Bunday banner topilmadi!"}, status=404)

    return JsonResponse({"success": False, "error": "❌ Xato so‘rov turi!"}, status=400)


@method_decorator(login_required, name='dispatch')
class LegacyPartnerInfoView(TemplateView):
    template_name = 'partners/partner.html'

    def get_context_data(self, **kwargs):
        """ Sahifa uchun kontekst ma'lumotlari """
        context = super().get_context_data(**kwargs)
        partner_id = self.request.GET.get("partner_id")

        if partner_id:
            context["partner_info"] = Partner.objects.filter(id=partner_id).first()
            # Agar partner_id mavjud bo‘lsa, breadcrumbs shu partiyaga moslashtiriladi
            partner = context["partner_info"]
            breadcrumbs = [
                {"title": "Bosh sahifa", "url": reverse('admin-index')},
                {"title": "Hamkorlar", "url": reverse('get-partner-info')},
                {"title": partner.name if partner else "Sherik", "url": "#", "active": True},
            ]
        else:
            context["partner_list"] = Partner.objects.all()  # Barcha ma'lumotlarni olish
            # Agar partner_id bo‘lmasa, umumiy sheriklar ro‘yxati uchun breadcrumbs
            breadcrumbs = [
                {"title": "Bosh sahifa", "url": reverse('admin-index')},
                {"title": "Hamkorlar", "url": reverse('get-partner-info'), "active": True},
            ]

        context["LANGUAGES"] = settings.LANGUAGES  # Tilni HTML-ga uzatish
        context["LANGUAGES_JSON"] = json.dumps([(code, str(name)) for code, name in settings.LANGUAGES])
        context["breadcrumbs"] = breadcrumbs  # Breadcrumb qo‘shildi

        return context

    def post(self, request):
        """ Yangi Doctor A ma'lumotini qo‘shish yoki mavjudini yangilash """
        partner_id = request.POST.get("partner_id")
        logo = request.FILES.get("logo")
        website_url = request.POST.get("website_url", "").strip()  # ✅ Website URL ni olish
        is_active = request.POST.get(
            "is_active") == "on"  # ✅ Formadan checkbox keladi, "on" bo'lsa True, aks holda False
        name = {code: request.POST.get(f'name[{code}]', "").strip() for code, _ in settings.LANGUAGES}
        description = {code: request.POST.get(f'description[{code}]', "").strip() for code, _ in settings.LANGUAGES}

        errors = []
        if not name.get("uz"):
            errors.append("📌 O'zbek tilida sarlavha kiritish majburiy.")
        if not description.get("uz"):
            errors.append("📌 O'zbek tilida tavsif kiritish majburiy.")
        if not partner_id and not logo:
            errors.append("📌 Rasm yuklash majburiy.")

        if website_url and not website_url.startswith(("http://", "https://")):
            errors.append(
                "📌 Veb-sayt manzili to‘g‘ri formatda bo‘lishi kerak (http:// yoki https:// bilan boshlanishi kerak).")

        if errors:
            return JsonResponse({"success": False, "error": "<br>".join(errors)}, status=400)

        # **Tahrirlash yoki yangi ma'lumot qo‘shish**
        if partner_id:  # **Tahrirlash**
            partner = get_object_or_404(Partner, id=partner_id)
            partner.name = name
            partner.description = description
            partner.website_url = website_url  # ✅ Website URL ni yangilash
            partner.is_active = is_active  # ✅ `is_active` ni yangilash
            if logo:
                partner.logo = logo  # Yangi rasm yuklangan bo‘lsa, almashtirish
            partner.save()
            return JsonResponse({"success": True, "message": "✅ Doctor A ma'lumotlari yangilandi!"})

        else:  # **Yangi qo‘shish**
            partner = Partner.objects.create(
                name=name,
                description=description,
                logo=logo,
                website_url=website_url,  # ✅ Yangi qo‘shishda website URL ni saqlash
                is_active=is_active  # ✅ `is_active` ni yangi qo‘shishda saqlash
            )
            return JsonResponse({"success": True, "message": "✅ Doctor A ma'lumotlari qo‘shildi!"})

    def clean_website_url(url):
        """ Website URL ni tozalash va kerakli formatda saqlash """
        url = url.strip()
        parsed_url = urlparse(url)

        if parsed_url.netloc.startswith("www."):
            return parsed_url.netloc[4:]  # `www.` ni olib tashlash
        return url  # O'zgarishsiz saqlash

    def patch(self, request):
        """ Ma'lumotni tahrirlash (rasmni ham yangilash) """
        print("🟡 PATCH so‘rovi kelib tushdi.")

        try:
            partner_id = request.POST.get("partner_id")
            name = json.loads(request.POST.get("name", "{}"))
            description = json.loads(request.POST.get("description", "{}"))
            logo = request.FILES.get("logo")  # 🔹 Rasmni olish
            website_url = request.POST.get("website_url", "").strip()  # ✅ Website URL ni olish
            is_active = request.POST.get("is_active") == "on"  # ✅ is_active ni olish

            print(f"📌 Olingan partner_id: {partner_id}")
            print("📖 Name ma'lumotlari:", name)
            print("📖 Description ma'lumotlari:", description)
            print("📷 Yuklangan rasm:", logo)
            print("🔗 Veb-sayt manzili:", website_url)
            print("⚡ Holati (is_active):", is_active)

            if not partner_id:
                print("🔴 Xatolik: partner_id kiritilmagan!")
                return JsonResponse({"success": False, "error": "❌ ID kiritilishi shart!"}, status=400)

            partner = get_object_or_404(Partner, id=partner_id)
            print(f"🟢 Partner ma'lumotlari topildi: {partner}")

            # 🔹 Yangilash
            partner.name = name
            partner.description = description
            partner.website_url = website_url  # ✅ Website URL ni yangilash
            partner.is_active = is_active  # ✅ `is_active` ni yangilash

            if logo:
                partner.logo = logo  # 🔹 Agar rasm yuklangan bo‘lsa, yangilash
                print("🖼️ Rasm yangilandi!")

            partner.save()
            print("✅ Partner ma'lumotlari yangilandi!")

            return JsonResponse({"success": True, "message": "✅ Partner ma'lumotlari yangilandi!"})

        except json.JSONDecodeError:
            print("🔴 Xatolik: JSON formati noto‘g‘ri!")
            return JsonResponse({"success": False, "error": "❌ Noto‘g‘ri JSON formati!"}, status=400)

    def delete(self, request):
        """ Ma'lumotni o‘chirish """
        try:
            data = json.loads(request.body)
            partner_id = data.get("partner_id")

            if not partner_id:
                print("🔴 Xatolik: ID kiritilmagan!")
                return JsonResponse({"success": False, "error": "❌ ID kiritilishi shart!"}, status=400)

            partner = get_object_or_404(Partner, id=partner_id)
            partner.delete()
            print(f"🟢 Doctor ID={partner_id} muvaffaqiyatli o‘chirildi!")

            return JsonResponse({"success": True, "message": "✅ Partner ma'lumotlari o‘chirildi!"})

        except json.JSONDecodeError:
            print("🔴 Xatolik: JSON formati noto‘g‘ri!")
            return JsonResponse({"success": False, "error": "❌ Noto‘g‘ri JSON formati!"}, status=400)

@method_decorator(login_required, name='dispatch')
class PartnerInfoView(View):
    template_name = 'partners/partner.html'
    paginate_by = 8

    def get_queryset(self, request):
        partners = Partner.objects.all().order_by('-created_at')

        search_query = request.GET.get('q', '').strip()
        if search_query:
            search_filter = Q(website_url__icontains=search_query)
            if search_query.isdigit():
                search_filter |= Q(id=int(search_query))

            for code, _name in settings.LANGUAGES:
                search_filter |= Q(**{f'name__{code}__icontains': search_query})
                search_filter |= Q(**{f'description__{code}__icontains': search_query})

            partners = partners.filter(search_filter)

        status_filter = request.GET.get('status', '').strip()
        if status_filter == 'active':
            partners = partners.filter(is_active=True)
        elif status_filter == 'inactive':
            partners = partners.filter(is_active=False)

        return partners

    def get_form_state(self, request, form_data=None):
        if form_data is not None:
            return {
                'partner_id': form_data.get('partner_id', ''),
                'name': form_data.get('name', {}),
                'description': form_data.get('description', {}),
                'website_url': form_data.get('website_url', ''),
                'is_active': form_data.get('is_active', True),
                'logo_url': form_data.get('logo_url', ''),
            }

        edit_partner_id = request.GET.get('edit', '').strip()
        if edit_partner_id:
            partner = Partner.objects.filter(id=edit_partner_id).first()
            if partner:
                return {
                    'partner_id': partner.id,
                    'name': partner.name,
                    'description': partner.description,
                    'website_url': partner.website_url or '',
                    'is_active': partner.is_active,
                    'logo_url': partner.logo.url if partner.logo else '',
                }

        return {
            'partner_id': '',
            'name': {},
            'description': {},
            'website_url': '',
            'is_active': True,
            'logo_url': '',
        }

    def get_context_data(self, request, form_data=None):
        partners = self.get_queryset(request)
        paginator = Paginator(partners, self.paginate_by)
        page_obj = paginator.get_page(request.GET.get('page'))
        search_query = request.GET.get('q', '').strip()
        status_filter = request.GET.get('status', '').strip()
        page_query = {
            key: value
            for key, value in {
                'q': search_query,
                'status': status_filter,
            }.items()
            if value
        }
        all_partners = Partner.objects.all()
        form_state = self.get_form_state(request, form_data=form_data)

        return {
            'partners': page_obj,
            'search_query': search_query,
            'status_filter': status_filter,
            'page_query': urlencode(page_query),
            'total_count': all_partners.count(),
            'active_count': all_partners.filter(is_active=True).count(),
            'inactive_count': all_partners.filter(is_active=False).count(),
            'filtered_count': partners.count(),
            'form_partner_id': form_state['partner_id'],
            'form_name': form_state['name'],
            'form_description': form_state['description'],
            'form_website_url': form_state['website_url'],
            'form_is_active': form_state['is_active'],
            'form_logo_url': form_state['logo_url'],
            'LANGUAGES': settings.LANGUAGES,
            'breadcrumbs': [
                {"title": "Bosh sahifa", "url": reverse('admin-index')},
                {"title": "Hamkorlar", "url": reverse('partners-info'), "active": True},
            ],
        }

    def get(self, request):
        return render(request, self.template_name, self.get_context_data(request))

    def post(self, request):
        action = request.POST.get('action', 'save')
        partner_id = request.POST.get('partner_id', '').strip()

        if action == 'delete':
            if not partner_id:
                messages.error(request, "Hamkor ID kiritilmadi.")
                return redirect('partners-info')

            partner = get_object_or_404(Partner, id=partner_id)
            partner.delete()
            messages.success(request, "Hamkor muvaffaqiyatli o'chirildi.")
            return redirect('partners-info')

        logo = request.FILES.get('logo')
        website_url = request.POST.get('website_url', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        name = {code: request.POST.get(f'name_{code}', '').strip() for code, _ in settings.LANGUAGES}
        description = {code: request.POST.get(f'description_{code}', '').strip() for code, _ in settings.LANGUAGES}

        current_partner = Partner.objects.filter(id=partner_id).first() if partner_id else None
        form_data = {
            'partner_id': partner_id,
            'name': name,
            'description': description,
            'website_url': website_url,
            'is_active': is_active,
            'logo_url': current_partner.logo.url if current_partner and current_partner.logo else '',
        }

        errors = []
        if not name.get('uz'):
            errors.append("O'zbek tilida nom majburiy.")
        if not description.get('uz'):
            errors.append("O'zbek tilida tavsif majburiy.")
        if not partner_id and not logo:
            errors.append("Logo yuklash majburiy.")
        if website_url and not website_url.startswith(('http://', 'https://')):
            errors.append("Veb-sayt manzili http:// yoki https:// bilan boshlanishi kerak.")

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, self.template_name, self.get_context_data(request, form_data=form_data))

        if partner_id:
            partner = get_object_or_404(Partner, id=partner_id)
            partner.name = name
            partner.description = description
            partner.website_url = website_url
            partner.is_active = is_active
            if logo:
                partner.logo = logo
            partner.save()
            messages.success(request, "Hamkor muvaffaqiyatli yangilandi.")
        else:
            partner = Partner(
                name=name,
                description=description,
                website_url=website_url,
                is_active=is_active,
            )
            if logo:
                partner.logo = logo
            partner.save()
            messages.success(request, "Hamkor muvaffaqiyatli qo'shildi.")

        return redirect('partners-info')

    def delete(self, request):
        """Eski AJAX delete so'rovlari uchun qoldirildi."""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Noto'g'ri JSON formati."}, status=400)

        partner_id = data.get("partner_id")
        if not partner_id:
            return JsonResponse({"success": False, "error": "Hamkor ID kiritilishi shart."}, status=400)

        partner = get_object_or_404(Partner, id=partner_id)
        partner.delete()
        return JsonResponse({"success": True, "message": "Hamkor muvaffaqiyatli o'chirildi."})


@login_required
@csrf_exempt  # CSRF muammolarni oldini olish uchun
def get_partner_info(request):
    """ AJAX orqali partner ma'lumotlarini olish """
    if request.method != "GET":
        return JsonResponse({"error": "❌ Faqat GET so‘rovlarga ruxsat berilgan!"}, status=405)

    partner_id = request.GET.get("partner_id")
    if not partner_id:
        return JsonResponse({"error": "❌ Partner ID ko‘rsatilishi shart!"}, status=400)

    # Partner ma'lumotini olish yoki 404 qaytarish
    partner = get_object_or_404(Partner, id=partner_id)

    data = {
        "id": partner.id,
        "logo_url": partner.logo.url if partner.logo else "",
        "name": partner.name,  # JSON formatda
        "description": partner.description,  # JSON formatda
        "website_url": partner.website_url if partner.website_url else ""  # ✅ Website URL qo'shildi
    }

    return JsonResponse(data)  # 🔹 JSON formatda qaytarish


@method_decorator(login_required, name='dispatch')
class ContactPhoneView(TemplateView):
    template_name = 'views/contact-phone.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


@method_decorator(login_required, name='dispatch')
class ContactPhoneView(TemplateView):
    """ ContactPhone CRUD (Create, Update, Delete) """
    template_name = 'views/contact-phone.html'

    def get_context_data(self, **kwargs):
        """ Barcha telefon raqamlarini olish """
        context = super().get_context_data(**kwargs)
        context["phones"] = ContactPhone.objects.all()
        context["LANGUAGES"] = settings.LANGUAGES
        context["LANGUAGES_JSON"] = json.dumps([(code, str(name)) for code, name in settings.LANGUAGES])
        return context

    def dispatch(self, request, *args, **kwargs):
        """ Request methodiga qarab funksiya chaqiriladi """
        if request.method == "POST":
            return self.create_phone(request)
        elif request.method == "PATCH":
            return self.update_phone(request)
        elif request.method == "DELETE":
            return self.delete_phone(request)
        return super().dispatch(request, *args, **kwargs)

    def create_phone(self, request):
        """ Yangi telefon raqamini qo‘shish """
        try:
            data = json.loads(request.body)
            phone_number = data.get("phone_number")
            description = data.get("description", {})

            if not phone_number:
                return JsonResponse({"success": False, "error": "📌 Telefon raqami kiritilishi shart!"}, status=400)

            phone = ContactPhone.objects.create(phone_number=phone_number, description=description)
            return JsonResponse(
                {"success": True, "message": "✅ Telefon raqami muvaffaqiyatli qo‘shildi!", "phone_id": phone.id})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "❌ JSON formati noto‘g‘ri!"}, status=400)

    def update_phone(self, request):
        """ Telefon raqamini yangilash """
        try:
            data = json.loads(request.body)
            phone_id = data.get("phone_id")
            phone_number = data.get("phone_number")
            description = data.get("description", {})

            if not phone_id or not phone_number:
                return JsonResponse({"success": False, "error": "📌 ID va telefon raqami kiritilishi shart!"},
                                    status=400)

            phone = get_object_or_404(ContactPhone, id=phone_id)
            phone.phone_number = phone_number
            phone.description = description
            phone.save()

            return JsonResponse({"success": True, "message": "✅ Telefon raqami yangilandi!"})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "❌ JSON formati noto‘g‘ri!"}, status=400)

    def delete_phone(self, request):
        """ Telefon raqamini o‘chirish """
        try:
            data = json.loads(request.body)
            phone_id = data.get("phone_id")

            if not phone_id:
                return JsonResponse({"success": False, "error": "📌 ID kiritilishi shart!"}, status=400)

            phone = get_object_or_404(ContactPhone, id=phone_id)
            phone.delete()

            return JsonResponse({"success": True, "message": "✅ Telefon raqami o‘chirildi!"})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "❌ JSON formati noto‘g‘ri!"}, status=400)


@login_required
def get_contact_phone(request):
    """ Foydalanuvchi tomonidan tanlangan telefon raqamini olish """
    phone_id = request.GET.get("phone_id")

    if not phone_id:
        return JsonResponse({"success": False, "error": "📌 Telefon raqam ID kiritilishi shart!"}, status=400)

    phone = get_object_or_404(ContactPhone, id=phone_id)

    return JsonResponse({
        "id": phone.id,
        "phone_number": phone.phone_number,
        "description": phone.description
    })


@method_decorator(login_required, name='dispatch')
class UsersView(View):
    template_name = 'havfsizlik/users.html'

    def get(self, request, *args, **kwargs):
        """ GET so‘rovlar uchun foydalanuvchilar ro‘yxatini ko‘rsatish """
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ POST so‘rovlar uchun foydalanuvchini o‘chirish """
        user_id = request.POST.get('user_id')  # Modal yoki formadan keladigan ID
        if user_id:
            try:
                user = CustomUser.objects.get(id=user_id)
                user.delete()
                messages.success(request, f"{user.full_name} muvaffaqiyatli o‘chirildi.")
            except CustomUser.DoesNotExist:
                messages.error(request, "Foydalanuvchi topilmadi.")
            except Exception as e:
                messages.error(request, f"Xatolik yuz berdi: {str(e)}")
        else:
            messages.error(request, "Foydalanuvchi ID topilmadi.")

        # O‘chirishdan so‘ng foydalanuvchilar ro‘yxatiga qaytish
        return redirect('users-view')

    def get_context_data(self, **kwargs):
        """ Foydalanuvchilar uchun kontekst yaratish """
        search_query = self.request.GET.get('search', '').strip()
        page = self.request.GET.get('page', 1)

        users = CustomUser.objects.all()

        if search_query:
            users = users.filter(
                Q(full_name__icontains=search_query) |
                Q(phone_number__icontains=search_query) |
                Q(job_title__icontains=search_query) |
                Q(department__icontains=search_query)
            )

        paginator = Paginator(users, 10)  # Har bir sahifada 10 ta foydalanuvchi
        paginated_users = paginator.get_page(page)

        # Jins va faollik statistikasi
        female_count = CustomUser.objects.filter(gender='female').count()
        all_count = CustomUser.objects.all().count()
        male_count = CustomUser.objects.filter(gender='male').count()
        inactive_count = CustomUser.objects.filter(is_active=False).count()

        # Breadcrumb uchun kontekst
        breadcrumbs = [
            {"title": "Bosh sahifa", "url": "{% url 'admin-index' %}"},
            {"title": "Foydalanuvchilar", "url": "{% url 'users-view' %}", "active": True},
        ]

        context = {
            "users": paginated_users,
            "search_query": search_query,
            "LANGUAGES": settings.LANGUAGES,
            "total_pages": paginator.num_pages,
            "current_page": paginated_users.number,
            "has_next": paginated_users.has_next(),
            "has_previous": paginated_users.has_previous(),
            "breadcrumbs": breadcrumbs,
            "female_count": female_count,  # Ayol foydalanuvchilar soni
            "all_count": all_count,  # Barcha foydalanuvchilar soni
            "male_count": male_count,  # Erkak foydalanuvchilar soni
            "inactive_count": inactive_count,  # Faol bo‘lmagan foydalanuvchilar soni
        }
        return context


@method_decorator(login_required, name='dispatch')
class AddUsersView(View):
    template_name = 'havfsizlik/add-users.html'

    def get(self, request, *args, **kwargs):
        """ GET so‘rovlar uchun forma ko‘rsatish """
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ POST so‘rov bilan foydalanuvchini yaratish """
        for key, value in request.POST.items():
            print(f"  - {key}: {value}")

        if request.FILES:
            for key, file in request.FILES.items():
                print(f"  - {key}: {file.name} ({file.content_type})")

        # Majburiy maydonlarni olish
        full_name = request.POST.get("full_name")
        phone_number = request.POST.get("phone_number")
        gender = request.POST.get("gender")
        username = request.POST.get("username")
        address = request.POST.get("address")
        emergency_contact = request.POST.get("emergency_contact")
        employment_date = request.POST.get("employment_date")
        employee_id = request.POST.get("employee_id")
        bio = CustomUser.normalize_rich_text_content(request.POST.get("bio"))
        nationality = request.POST.get("nationality")
        professional_license_number = request.POST.get("professional_license_number")
        bank_account_number = request.POST.get("bank_account_number")
        tax_identification_number = request.POST.get("tax_identification_number")
        insurance_number = request.POST.get("insurance_number")
        shift_schedule = request.POST.get("shift_schedule")
        medical_specialty = request.POST.get("medical_specialty")
        date_of_birth = request.POST.get("date_of_birth")
        contract_end_date = request.POST.get("contract_end_date")
        department = request.POST.get("department")
        job_title = request.POST.get("job_title")
        is_active = request.POST.get("is_active") == "on"
        work_start_time = request.POST.get("work_start_time")
        work_end_time = request.POST.get("work_end_time")
        telegram_username = request.POST.get("telegram_username")
        instagram_username = request.POST.get("instagram_username")
        profile_picture = request.FILES.get("profile_picture")

        # Majburiy maydonlarni tekshirish
        if not full_name or not phone_number or not gender:
            print("❌ Xatolik: Majburiy maydonlar to‘ldirilmagan!")
            messages.error(request, "Majburiy maydonlarni to‘ldiring: F.I.O, Telefon raqami va Jins!")
            return redirect('add-user')

        # Sana va vaqt maydonlarini tekshirish uchun funksiyalar
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return None

        def parse_time(time_str):
            if not time_str:
                return None
            try:
                return datetime.strptime(time_str, '%H:%M').time()
            except ValueError:
                return None

        # Sana va vaqt maydonlarini to'g'rilash
        date_of_birth = parse_date(date_of_birth)
        employment_date = parse_date(employment_date)
        contract_end_date = parse_date(contract_end_date)
        work_start_time = parse_time(work_start_time)
        work_end_time = parse_time(work_end_time)

        # Foydalanuvchi yaratish
        print("🚀 Yangi foydalanuvchi yaratish jarayoni boshlandi...")
        try:
            user = CustomUser(
                full_name=full_name,
                username=username or "",
                address=address or "",
                emergency_contact=emergency_contact or "",
                insurance_number=insurance_number or "",
                shift_schedule=shift_schedule or "",
                employment_date=employment_date,
                tax_identification_number=tax_identification_number or "",
                medical_specialty=medical_specialty or "",
                bank_account_number=bank_account_number or "",
                contract_end_date=contract_end_date,
                professional_license_number=professional_license_number or "",
                department=department or "",
                bio=bio or "",
                nationality=nationality or "",
                employee_id=employee_id or "",
                phone_number=phone_number,
                gender=gender,
                date_of_birth=date_of_birth,
                job_title=job_title or "",
                is_active=is_active,
                profile_picture=profile_picture,
                work_start_time=work_start_time,
                work_end_time=work_end_time,
                telegram_username=telegram_username or "",
                instagram_username=instagram_username or ""
            )

            # Telegram kanaliga xabar yuborish
            message_text = (
                f"👤 <b>Yangi foydalanuvchi qo‘shildi!</b>\n"
                f"#_<b>ADD_USER</b>\n"
                f"📌 Ismi: {full_name}\n"
                f"📛 Foydalanuvchi nomi: {username or 'Belgilanmagan'}\n"
                f"📞 Telefon: {phone_number}\n"
                f"🏠 Manzil: {address or 'Belgilanmagan'}\n"
                f"🎂 Tug‘ilgan sana: {date_of_birth or 'Belgilanmagan'}\n"
                f"⚥ Jinsi: {'Erkak' if gender == 'male' else 'Ayol'}\n"
                f"🌍 Millati: {nationality or 'Belgilanmagan'}\n"
                f"🆔 Xodim ID: {employee_id or 'Belgilanmagan'}\n"
                f"📝 Bio: {bio or 'Belgilanmagan'}\n"
                f"🚑 Favqulodda aloqa: {emergency_contact or 'Belgilanmagan'}\n"
                f"🏢 Bo‘lim: {department or 'Belgilanmagan'}\n"
                f"💼 Lavozim: {job_title or 'Belgilanmagan'}\n"
                f"📅 Ishga kirgan sana: {employment_date or 'Belgilanmagan'}\n"
                f"📆 Shartnoma muddati: {contract_end_date or 'Belgilanmagan'}\n"
                f"🔢 Professional litsenziya raqami: {professional_license_number or 'Belgilanmagan'}\n"
                f"🩺 Tibbiy mutaxassisligi: {medical_specialty or 'Belgilanmagan'}\n"
                f"⏰ Ish jadvali: {shift_schedule or 'Belgilanmagan'}\n"
                f"🏦 Bank hisobi: {bank_account_number or 'Belgilanmagan'}\n"
                f"🆔 Soliq identifikatsiya raqami: {tax_identification_number or 'Belgilanmagan'}\n"
                f"🛡 Sug‘urta raqami: {insurance_number or 'Belgilanmagan'}\n"
                f"🟢 Holati: {'Faol' if is_active else 'Faol emas'}"
            )
            send_message(message_text)

            user.save()
            print(f"✅ Foydalanuvchi qo‘shildi: {user.full_name} (ID: {user.id})")
            messages.success(request, f"{user.full_name} muvaffaqiyatli qo‘shildi!")
            return redirect('users-view')

        except Exception as e:
            print(f"❌ Xatolik: {str(e)}")
            messages.error(request, f"Hodim qo‘shishda xatolik yuz berdi: {str(e)}")
            return redirect('add-users-view')

    def get_context_data(self, **kwargs):
        """ Kontekst yaratish, shu jumladan breadcrumb """
        context = {}
        breadcrumbs = [
            {"title": "Bosh sahifa", "url": reverse('admin-index')},
            {"title": "Foydalanuvchilar", "url": reverse('users-view')},
            {"title": "Foydalanuvchi qo‘shish", "url": reverse('add-users-view'), "active": True},
        ]
        context["breadcrumbs"] = breadcrumbs
        return context


# ✅ Sana formatini xavfsiz tarzda o‘zgartiruvchi funksiya
def parse_date_safe(date_str):
    if date_str and date_str.strip():
        try:
            return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        except ValueError:
            print(f"[WARN] ❗ Yaroqsiz sana: '{date_str}'")
            return None
    return None

# ✅ Vaqt formatini xavfsiz tarzda o‘zgartiruvchi funksiya
def parse_time_safe(time_str):
    if time_str and time_str.strip():
        try:
            return datetime.strptime(time_str.strip(), "%H:%M").time()
        except ValueError:
            print(f"[WARN] ❗ Yaroqsiz vaqt: '{time_str}'")
            return None
    return None


@method_decorator(login_required, name='dispatch')
class EditUsersView(View):
    template_name = 'havfsizlik/edit-users.html'

    def get(self, request, user_id, *args, **kwargs):
        print(f"\n[GET] 🔍 Tahrirlash sahifasi ochildi | user_id = {user_id}")
        user = get_object_or_404(CustomUser, id=user_id)
        context = self.get_context_data(user=user, **kwargs)
        context['user'] = user
        print(f"[GET] 📎 User: {user.full_name}, Username: {user.username}")
        print(f"[GET] 🧭 Breadcrumbs: {context['breadcrumbs']}")
        return render(request, self.template_name, context)

    def post(self, request, user_id, *args, **kwargs):
        print(f"\n[POST] 📝 Tahrirlash so‘rovi kelib tushdi | user_id = {user_id}")
        user = get_object_or_404(CustomUser, id=user_id)
        data = request.POST
        profile_picture = request.FILES.get("profile_picture")

        # Majburiy maydonlar
        full_name = data.get("full_name")
        phone_number = data.get("phone_number")
        gender = data.get("gender")
        bio = CustomUser.normalize_rich_text_content(data.get("bio"))

        print("="*50)
        print(f"DEBUG BIO (Raw from request): {bio}")
        print("="*50)

        if not full_name or not phone_number or not gender:
            print("[POST] ❌ Majburiy maydonlar to‘ldirilmagan!")
            messages.error(request, "Majburiy maydonlarni to‘ldiring: F.I.O, Telefon raqami va Jins!")
            return redirect('edit-user', user_id=user_id)

        try:
            user.full_name = full_name
            user.username = data.get("username", "")
            user.phone_number = phone_number
            user.gender = gender
            user.address = data.get("address") or ""
            user.emergency_contact = data.get("emergency_contact") or ""
            user.employment_date = parse_date_safe(data.get("employment_date"))
            user.employee_id = data.get("employee_id") or ""
            user.bio = bio or ""
            user.nationality = data.get("nationality") or ""
            user.professional_license_number = data.get("professional_license_number") or ""
            user.bank_account_number = data.get("bank_account_number") or ""
            user.tax_identification_number = data.get("tax_identification_number") or ""
            user.insurance_number = data.get("insurance_number") or ""
            user.shift_schedule = data.get("shift_schedule") or ""
            user.medical_specialty = data.get("medical_specialty") or ""
            user.date_of_birth = parse_date_safe(data.get("date_of_birth"))
            user.contract_end_date = parse_date_safe(data.get("contract_end_date"))
            user.department = data.get("department") or ""
            user.job_title = data.get("job_title") or ""
            user.is_active = data.get("is_active") == "on"
            user.work_start_time = parse_time_safe(data.get("work_start_time"))
            user.work_end_time = parse_time_safe(data.get("work_end_time"))
            user.telegram_username = data.get("telegram_username") or ""
            user.instagram_username = data.get("instagram_username") or ""

            if profile_picture:
                print("[POST] 📷 Yangi profil rasmi yuklandi")
                user.profile_picture = profile_picture

            user.save()
            print(f"[POST] ✅ Saqlash muvaffaqiyatli: {user.full_name} | ID: {user.id}")
            messages.success(request, f"{user.full_name} muvaffaqiyatli tahrirlandi!")
            return redirect('users-view')

        except Exception as e:
            print(f"[ERROR] ❌ Tahrirlashda xatolik yuz berdi: {str(e)}")
            traceback.print_exc()
            messages.error(request, f"Tahrirlashda xatolik yuz berdi: {str(e)}")
            return redirect('edit-user', user_id=user_id)

    def get_context_data(self, **kwargs):
        user = kwargs.get('user')
        breadcrumbs = [
            {"title": "Bosh sahifa", "url": reverse('admin-index')},
            {"title": "Foydalanuvchilar", "url": reverse('users-view')},
            {"title": f"{user.full_name if user else 'Foydalanuvchi'} tahrirlash", "url": "", "active": True},
        ]
        return {"breadcrumbs": breadcrumbs}


def normalize_user_phone(value):
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    if digits.startswith("998"):
        digits = digits[3:]
    digits = digits[:9]

    if not digits:
        return ""

    parts = [
        digits[:2],
        digits[2:5],
        digits[5:7],
        digits[7:9],
    ]
    return "+998 " + " ".join(part for part in parts if part)


class UserFormMixin:
    template_name = "havfsizlik/user-form.html"

    def get_user_object(self):
        user_id = self.kwargs.get("user_id")
        if not user_id:
            return None
        return get_object_or_404(CustomUser, id=user_id)

    def get_initial_form_data(self, user=None):
        return {
            "full_name": user.full_name if user else "",
            "username": user.username if user else "",
            "phone_number": normalize_user_phone(user.phone_number) if user and user.phone_number else "",
            "employee_id": user.employee_id if user and user.employee_id else "",
            "gender": user.gender if user else "",
            "date_of_birth": user.date_of_birth.strftime("%Y-%m-%d") if user and user.date_of_birth else "",
            "job_title": user.job_title if user else "",
            "department": user.department if user else "",
            "nationality": user.nationality if user else "",
            "emergency_contact": normalize_user_phone(user.emergency_contact) if user and user.emergency_contact else "",
            "work_start_time": user.work_start_time.strftime("%H:%M") if user and user.work_start_time else "",
            "work_end_time": user.work_end_time.strftime("%H:%M") if user and user.work_end_time else "",
            "insurance_number": user.insurance_number if user else "",
            "telegram_username": user.telegram_username if user else "",
            "instagram_username": user.instagram_username if user else "",
            "employment_date": user.employment_date.strftime("%Y-%m-%d") if user and user.employment_date else "",
            "contract_end_date": user.contract_end_date.strftime("%Y-%m-%d") if user and user.contract_end_date else "",
            "professional_license_number": user.professional_license_number if user else "",
            "medical_specialty": user.medical_specialty if user else "",
            "shift_schedule": user.shift_schedule if user else "",
            "bank_account_number": user.bank_account_number if user else "",
            "tax_identification_number": user.tax_identification_number if user else "",
            "bio": user.get_clean_bio() if user else "",
            "address": user.address if user else "",
            "is_active": user.is_active if user else True,
        }

    def get_form_data(self, request, user=None):
        return {
            "full_name": request.POST.get("full_name", "").strip(),
            "username": request.POST.get("username", "").strip(),
            "phone_number": normalize_user_phone(request.POST.get("phone_number", "")),
            "employee_id": request.POST.get("employee_id", "").strip(),
            "gender": request.POST.get("gender", "").strip(),
            "date_of_birth": request.POST.get("date_of_birth", "").strip(),
            "job_title": request.POST.get("job_title", "").strip(),
            "department": request.POST.get("department", "").strip(),
            "nationality": request.POST.get("nationality", "").strip(),
            "emergency_contact": normalize_user_phone(request.POST.get("emergency_contact", "")),
            "work_start_time": request.POST.get("work_start_time", "").strip(),
            "work_end_time": request.POST.get("work_end_time", "").strip(),
            "insurance_number": request.POST.get("insurance_number", "").strip(),
            "telegram_username": request.POST.get("telegram_username", "").strip(),
            "instagram_username": request.POST.get("instagram_username", "").strip(),
            "employment_date": request.POST.get("employment_date", "").strip(),
            "contract_end_date": request.POST.get("contract_end_date", "").strip(),
            "professional_license_number": request.POST.get("professional_license_number", "").strip(),
            "medical_specialty": request.POST.get("medical_specialty", "").strip(),
            "shift_schedule": request.POST.get("shift_schedule", "").strip(),
            "bank_account_number": request.POST.get("bank_account_number", "").strip(),
            "tax_identification_number": request.POST.get("tax_identification_number", "").strip(),
            "bio": CustomUser.normalize_rich_text_content(request.POST.get("bio")),
            "address": request.POST.get("address", "").strip(),
            "is_active": request.POST.get("is_active") == "on",
        }

    def resolve_username(self, form_data, user=None):
        candidate = form_data.get("username", "").strip()
        if not candidate and user and user.username:
            candidate = user.username.strip()

        if not candidate:
            fallback = (
                form_data.get("employee_id")
                or "".join(ch for ch in form_data.get("phone_number", "") if ch.isdigit())
                or form_data.get("full_name")
                or "user"
            )
            candidate = slugify(fallback)[:150]

        candidate = candidate[:150] or "user"
        queryset = CustomUser.objects.all()
        if user:
            queryset = queryset.exclude(pk=user.pk)

        base_candidate = candidate
        suffix = 1
        while queryset.filter(username=candidate).exists():
            suffix_text = f"-{suffix}"
            candidate = f"{base_candidate[:150 - len(suffix_text)]}{suffix_text}"
            suffix += 1

        return candidate

    def validate_form_data(self, form_data):
        errors = []
        if not form_data["full_name"]:
            errors.append("F.I.O majburiy.")
        if not form_data["phone_number"]:
            errors.append("Telefon raqami majburiy.")
        if not form_data["gender"]:
            errors.append("Jins majburiy.")
        return errors

    def apply_form_data(self, user, form_data, profile_picture=None):
        user.full_name = form_data["full_name"]
        user.username = self.resolve_username(form_data, user=user if user.pk else None)
        user.phone_number = form_data["phone_number"]
        user.employee_id = form_data["employee_id"] or ""
        user.gender = form_data["gender"]
        user.date_of_birth = parse_date_safe(form_data["date_of_birth"])
        user.job_title = form_data["job_title"] or ""
        user.department = form_data["department"] or ""
        user.nationality = form_data["nationality"] or ""
        user.emergency_contact = form_data["emergency_contact"] or ""
        user.work_start_time = parse_time_safe(form_data["work_start_time"])
        user.work_end_time = parse_time_safe(form_data["work_end_time"])
        user.insurance_number = form_data["insurance_number"] or ""
        user.telegram_username = form_data["telegram_username"] or ""
        user.instagram_username = form_data["instagram_username"] or ""
        user.employment_date = parse_date_safe(form_data["employment_date"])
        user.contract_end_date = parse_date_safe(form_data["contract_end_date"])
        user.professional_license_number = form_data["professional_license_number"] or ""
        user.medical_specialty = form_data["medical_specialty"] or ""
        user.shift_schedule = form_data["shift_schedule"] or ""
        user.bank_account_number = form_data["bank_account_number"] or ""
        user.tax_identification_number = form_data["tax_identification_number"] or ""
        user.bio = form_data["bio"] or ""
        user.address = form_data["address"] or ""
        user.is_active = form_data["is_active"]
        user.is_active_employee = form_data["is_active"]

        if profile_picture:
            user.profile_picture = profile_picture

        return user

    def get_context_data(self, request, user=None, form_data=None):
        if form_data is None:
            form_data = self.get_initial_form_data(user=user)

        is_edit = user is not None
        page_title = "Foydalanuvchini tahrirlash" if is_edit else "Foydalanuvchi qo'shish"
        page_subtitle = (
            "Xodim ma'lumotlarini yangilang va profilini boshqaring."
            if is_edit
            else "Yangi xodim uchun barcha kerakli ma'lumotlarni kiriting."
        )

        return {
            "form": form_data,
            "user_obj": user,
            "page_title": page_title,
            "page_subtitle": page_subtitle,
            "submit_label": "Saqlash" if is_edit else "Qo'shish",
            "profile_preview_url": user.profile_picture.url if user and user.profile_picture else "",
            "breadcrumbs": [
                {"title": "Bosh sahifa", "url": reverse("admin-index")},
                {"title": "Foydalanuvchilar", "url": reverse("users-view")},
                {
                    "title": page_title,
                    "url": reverse("edit-user", kwargs={"user_id": user.id}) if is_edit else reverse("add-users-view"),
                    "active": True,
                },
            ],
        }


@method_decorator(login_required, name="dispatch")
class UsersView(View):
    template_name = "havfsizlik/users.html"
    paginate_by = 12

    def get_queryset(self, request):
        users = CustomUser.objects.all().order_by("-date_joined", "full_name", "username")
        search_query = request.GET.get("q", request.GET.get("search", "")).strip()
        status_filter = request.GET.get("status", "").strip()

        if search_query:
            users = users.filter(
                Q(full_name__icontains=search_query)
                | Q(username__icontains=search_query)
                | Q(phone_number__icontains=search_query)
                | Q(employee_id__icontains=search_query)
                | Q(job_title__icontains=search_query)
                | Q(department__icontains=search_query)
                | Q(nationality__icontains=search_query)
            )

        if status_filter == "active":
            users = users.filter(is_active=True)
        elif status_filter == "inactive":
            users = users.filter(is_active=False)

        return users

    def get_context_data(self, request):
        users_queryset = self.get_queryset(request)
        paginator = Paginator(users_queryset, self.paginate_by)
        users = paginator.get_page(request.GET.get("page"))
        search_query = request.GET.get("q", request.GET.get("search", "")).strip()
        status_filter = request.GET.get("status", "").strip()
        page_query = {
            key: value
            for key, value in {
                "q": search_query,
                "status": status_filter,
            }.items()
            if value
        }
        all_users = CustomUser.objects.all()

        return {
            "users": users,
            "search_query": search_query,
            "status_filter": status_filter,
            "page_query": urlencode(page_query),
            "current_path": request.get_full_path(),
            "total_count": all_users.count(),
            "active_count": all_users.filter(is_active=True).count(),
            "inactive_count": all_users.filter(is_active=False).count(),
            "filtered_count": users_queryset.count(),
            "breadcrumbs": [
                {"title": "Bosh sahifa", "url": reverse("admin-index")},
                {"title": "Foydalanuvchilar", "url": reverse("users-view"), "active": True},
            ],
        }

    def redirect_to_list(self, request):
        return_path = request.POST.get("return_path", "").strip()
        if return_path.startswith("/"):
            return redirect(return_path)
        return redirect("users-view")

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data(request))

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action", "").strip()
        user_id = request.POST.get("user_id", "").strip()

        if not user_id:
            messages.error(request, "Foydalanuvchi ID topilmadi.")
            return self.redirect_to_list(request)

        user = get_object_or_404(CustomUser, id=user_id)

        if action == "delete":
            full_name = user.full_name or user.username
            user.delete()
            messages.success(request, f"{full_name} muvaffaqiyatli o'chirildi.")
            return self.redirect_to_list(request)

        if action == "update_status":
            status = request.POST.get("status", "").strip()
            if status not in {"active", "inactive"}:
                messages.error(request, "Status noto'g'ri yuborildi.")
                return self.redirect_to_list(request)

            is_active = status == "active"
            user.is_active = is_active
            user.is_active_employee = is_active
            user.save(update_fields=["is_active", "is_active_employee"])
            messages.success(request, "Foydalanuvchi holati yangilandi.")
            return self.redirect_to_list(request)

        messages.error(request, "Noto'g'ri amal yuborildi.")
        return self.redirect_to_list(request)


@method_decorator(login_required, name="dispatch")
class AddUsersView(UserFormMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data(request))

    def post(self, request, *args, **kwargs):
        form_data = self.get_form_data(request)
        errors = self.validate_form_data(form_data)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, self.template_name, self.get_context_data(request, form_data=form_data))

        profile_picture = request.FILES.get("profile_picture")

        try:
            user = self.apply_form_data(CustomUser(), form_data, profile_picture=profile_picture)
            user.save()

            try:
                send_message(
                    "👤 <b>Yangi foydalanuvchi qo'shildi</b>\n"
                    "#_<b>ADD_USER</b>\n"
                    f"F.I.O: {user.full_name}\n"
                    f"Username: {user.username}\n"
                    f"Telefon: {user.phone_number}\n"
                    f"Bo'lim: {user.department or '-'}\n"
                    f"Lavozim: {user.job_title or '-'}"
                )
            except Exception:
                pass

            messages.success(request, f"{user.full_name} muvaffaqiyatli qo'shildi.")
            return redirect("users-view")
        except Exception as exc:
            messages.error(request, f"Foydalanuvchi qo'shishda xatolik yuz berdi: {exc}")
            return render(request, self.template_name, self.get_context_data(request, form_data=form_data))


@method_decorator(login_required, name="dispatch")
class EditUsersView(UserFormMixin, View):
    def get(self, request, user_id, *args, **kwargs):
        user = self.get_user_object()
        return render(request, self.template_name, self.get_context_data(request, user=user))

    def post(self, request, user_id, *args, **kwargs):
        user = self.get_user_object()
        form_data = self.get_form_data(request, user=user)
        errors = self.validate_form_data(form_data)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, self.template_name, self.get_context_data(request, user=user, form_data=form_data))

        profile_picture = request.FILES.get("profile_picture")

        try:
            self.apply_form_data(user, form_data, profile_picture=profile_picture)
            user.save()
            messages.success(request, f"{user.full_name} muvaffaqiyatli tahrirlandi.")
            return redirect("users-view")
        except Exception as exc:
            traceback.print_exc()
            messages.error(request, f"Tahrirlashda xatolik yuz berdi: {exc}")
            return render(request, self.template_name, self.get_context_data(request, user=user, form_data=form_data))

@method_decorator(login_required, name='dispatch')
class RolesView(TemplateView):
    template_name = 'havfsizlik/roles.html'
    paginate_by = 15

    def get_context_data(self, **kwargs):
        """ Sahifa uchun kontekst ma'lumotlari """
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get("q", "").strip()
        users = CustomUser.objects.prefetch_related("groups").order_by("full_name", "username")

        if search_query:
            users = users.filter(
                Q(full_name__icontains=search_query)
                | Q(username__icontains=search_query)
                | Q(email__icontains=search_query)
                | Q(job_title__icontains=search_query)
                | Q(department__icontains=search_query)
                | Q(groups__name__icontains=search_query)
            ).distinct()

        groups = Group.objects.prefetch_related("permissions").order_by("name")
        group_rows = [
            {
                "group": group,
                "user_count": CustomUser.objects.filter(groups=group).count(),
                "permissions_count": group.permissions.count(),
            }
            for group in groups
        ]

        paginator = Paginator(users, self.paginate_by)
        context["users"] = paginator.get_page(self.request.GET.get("page"))
        context["search_query"] = search_query
        context["groups"] = group_rows
        context["total_users"] = CustomUser.objects.count()
        context["superuser_count"] = CustomUser.objects.filter(is_superuser=True).count()
        context["staff_count"] = CustomUser.objects.filter(is_staff=True).count()
        context["employee_count"] = CustomUser.objects.filter(is_active_employee=True).count()
        context["inactive_count"] = CustomUser.objects.filter(is_active=False).count()
        context["system_roles"] = [
            {
                "name": "Super admin",
                "description": "Barcha bo'limlar, sozlamalar va foydalanuvchilarni boshqaradi.",
                "count": context["superuser_count"],
                "badge": "bg-danger-subtle text-danger",
            },
            {
                "name": "Admin panel foydalanuvchisi",
                "description": "Administrator paneliga kirish huquqiga ega.",
                "count": context["staff_count"],
                "badge": "bg-primary-subtle text-primary",
            },
            {
                "name": "Xodim",
                "description": "Klinika xodimi sifatida landing va qabul bo'limlarida ishlatiladi.",
                "count": context["employee_count"],
                "badge": "bg-success-subtle text-success",
            },
            {
                "name": "Nofaol foydalanuvchi",
                "description": "Tizimga kira olmaydigan yoki vaqtincha o'chirilgan foydalanuvchi.",
                "count": context["inactive_count"],
                "badge": "bg-secondary-subtle text-secondary",
            },
        ]

        return context

    def post(self, request, *args, **kwargs):
        role_name = request.POST.get("role_name", "").strip()
        if not role_name:
            messages.error(request, "Rol nomini kiriting.")
            return redirect("roles-view")

        if Group.objects.filter(name__iexact=role_name).exists():
            messages.error(request, "Bunday rol allaqachon mavjud.")
            return redirect("roles-view")

        Group.objects.create(name=role_name)
        messages.success(request, "Rol muvaffaqiyatli qo'shildi.")
        return redirect("roles-view")


@method_decorator(login_required, name='dispatch')
class LogsView(TemplateView):
    template_name = 'havfsizlik/logs.html'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        """ Sahifa uchun kontekst ma'lumotlari """
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get("q", "").strip()
        logs = Log.objects.select_related("user").order_by("-timestamp")

        if search_query:
            log_filter = (
                Q(path__icontains=search_query)
                | Q(ip_address__icontains=search_query)
                | Q(method__icontains=search_query)
                | Q(user__username__icontains=search_query)
                | Q(user__full_name__icontains=search_query)
            )
            if search_query.isdigit():
                log_filter |= Q(status_code=int(search_query))
            logs = logs.filter(log_filter)

        paginator = Paginator(logs, self.paginate_by)
        context["logs"] = paginator.get_page(self.request.GET.get("page"))
        context["search_query"] = search_query
        context["total_logs"] = logs.count()

        return context


@method_decorator(login_required, name='dispatch')
class AppointmentView(View):
    template_name = 'views/appointment.html'
    paginate_by = 10

    def get(self, request):
        """Qabullar ro'yxatini ko'rsatish."""
        appointments = Appointment.objects.select_related('employee').all().order_by('-created_at')

        search_query = request.GET.get('q', '').strip()
        if search_query:
            appointments = appointments.filter(
                Q(full_name__icontains=search_query)
                | Q(phone_number__icontains=search_query)
                | Q(message__icontains=search_query)
                | Q(employee__full_name__icontains=search_query)
                | Q(employee__username__icontains=search_query)
            )

        status_filter = request.GET.get('status', '').strip()
        if status_filter in {'pending', 'approved', 'canceled'}:
            appointments = appointments.filter(status=status_filter)

        paginator = Paginator(appointments, self.paginate_by)
        page_obj = paginator.get_page(request.GET.get('page'))
        page_query = {
            key: value
            for key, value in {
                "q": search_query,
                "status": status_filter,
            }.items()
            if value
        }

        all_appointments = Appointment.objects.all()
        return render(request, self.template_name, {
            "appointments": page_obj,
            "search_query": search_query,
            "status_filter": status_filter,
            "page_query": urlencode(page_query),
            "total_count": all_appointments.count(),
            "pending_count": all_appointments.filter(status='pending').count(),
            "approved_count": all_appointments.filter(status='approved').count(),
            "canceled_count": all_appointments.filter(status='canceled').count(),
            "filtered_count": appointments.count(),
            "breadcrumbs": [
                {"title": "Bosh sahifa", "url": reverse('admin-index')},
                {"title": "Qabullar", "url": reverse('appointment-view'), "active": True},
            ],
        })

    def post(self, request):
        """Qabulni o'chirish."""
        appointment_id = request.POST.get('appointment_id')
        if appointment_id:
            appointment = get_object_or_404(Appointment, id=appointment_id)
            appointment.delete()
            messages.success(request, "Qabul muvaffaqiyatli o'chirildi.")
        else:
            messages.error(request, "Qabul ID kiritilmadi.")
        return redirect('appointment-view')

    def delete(self, request):
        """Eski AJAX delete so'rovlari uchun qoldirildi."""
        appointment_id = request.GET.get('appointment_id')
        if not appointment_id:
            return JsonResponse({"success": False, "message": "Qabul ID kiritilmadi."}, status=400)

        appointment = get_object_or_404(Appointment, id=appointment_id)
        appointment.delete()
        return JsonResponse({"success": True, "message": "Qabul o'chirildi."})


@method_decorator(login_required, name='dispatch')
class AppointmentDetailView(View):
    template_name = 'views/appointment-detail.html'

    def get(self, request, pk):
        appointment = get_object_or_404(Appointment.objects.select_related('employee'), pk=pk)
        return render(request, self.template_name, {
            "appointment": appointment,
            "breadcrumbs": [
                {"title": "Bosh sahifa", "url": reverse('admin-index')},
                {"title": "Qabullar", "url": reverse('appointment-view')},
                {"title": appointment.full_name, "url": "", "active": True},
            ],
        })

    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        action = request.POST.get("action", "update_status")

        if action == "delete":
            appointment.delete()
            messages.success(request, "Qabul muvaffaqiyatli o'chirildi.")
            return redirect('appointment-view')

        status = request.POST.get("status")
        if status not in {"pending", "approved", "canceled"}:
            messages.error(request, "Status noto'g'ri yuborildi.")
            return redirect('appointment-detail', pk=appointment.pk)

        appointment.status = status
        appointment.save(update_fields=["status"])
        messages.success(request, "Qabul statusi yangilandi.")
        return redirect('appointment-detail', pk=appointment.pk)

@method_decorator(login_required, name='dispatch')
class LegacyMedicalCheckupApplicationView(View):
    template_name = 'views/medicalCheckup.html'
    paginate_by = 10  # Har bir sahifada 10 ta ariza

    def get(self, request):
        """ Arizalarni ko‘rsatish (qidirish + pagination) """
        applications = MedicalCheckupApplication.objects.all()

        # ✅ Qidiruv
        search_query = request.GET.get('q', '').strip()
        if search_query:
            applications = applications.filter(
                full_name__icontains=search_query
            ) | applications.filter(phone_number__icontains=search_query)

        # ✅ Pagination
        paginator = Paginator(applications.order_by('-created_at'), self.paginate_by)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Breadcrumb uchun kontekst
        breadcrumbs = [
            {"title": "Bosh sahifa", "url": reverse('admin-index')},
            {"title": "Tibbiy ko'rik arizalari", "url": reverse('medical-checkup-applications'), "active": True},
        ]

        context = {
            "applications": page_obj,
            "search_query": search_query,
            "breadcrumbs": breadcrumbs,
        }
        return render(request, self.template_name, context)

    def delete(self, request):
        """ Ariza o‘chirish """
        application_id = request.GET.get('application_id')
        if application_id:
            try:
                application = get_object_or_404(MedicalCheckupApplication, id=application_id)
                application.delete()
                return JsonResponse({"status": "success", "message": "Ariza muvaffaqiyatli o‘chirildi!"})
            except MedicalCheckupApplication.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Ariza topilmadi!"}, status=404)
        return JsonResponse({"status": "error", "message": "Ariza ID kiritilmadi!"}, status=400)

@method_decorator(login_required, name='dispatch')
class MedicalCheckupApplicationView(View):
    template_name = 'views/medicalCheckup.html'
    paginate_by = 10

    def get(self, request):
        """Arizalarni ko'rsatish."""
        applications = MedicalCheckupApplication.objects.all().order_by('-created_at')

        search_query = request.GET.get('q', '').strip()
        if search_query:
            applications = applications.filter(
                Q(full_name__icontains=search_query)
                | Q(phone_number__icontains=search_query)
                | Q(message__icontains=search_query)
            )

        status_filter = request.GET.get('status', '').strip()
        if status_filter == 'seen':
            applications = applications.filter(is_seen=True)
        elif status_filter == 'unseen':
            applications = applications.filter(is_seen=False)

        paginator = Paginator(applications, self.paginate_by)
        page_obj = paginator.get_page(request.GET.get('page'))
        page_query = {
            key: value
            for key, value in {
                "q": search_query,
                "status": status_filter,
            }.items()
            if value
        }

        all_applications = MedicalCheckupApplication.objects.all()
        context = {
            "applications": page_obj,
            "search_query": search_query,
            "status_filter": status_filter,
            "page_query": urlencode(page_query),
            "total_count": all_applications.count(),
            "seen_count": all_applications.filter(is_seen=True).count(),
            "unseen_count": all_applications.filter(is_seen=False).count(),
            "filtered_count": applications.count(),
            "breadcrumbs": [
                {"title": "Bosh sahifa", "url": reverse('admin-index')},
                {"title": "Tibbiy ko'rik arizalari", "url": reverse('medical-checkup-applications'), "active": True},
            ],
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Arizani o'chirish."""
        application_id = request.POST.get('application_id')
        if application_id:
            application = get_object_or_404(MedicalCheckupApplication, id=application_id)
            application.delete()
            messages.success(request, "Ariza muvaffaqiyatli o'chirildi.")
        else:
            messages.error(request, "Ariza ID kiritilmadi.")
        return redirect('medical-checkup-applications')

    def delete(self, request):
        """Eski AJAX delete so'rovlari uchun qoldirildi."""
        application_id = request.GET.get('application_id')
        if not application_id:
            return JsonResponse({"status": "error", "message": "Ariza ID kiritilmadi!"}, status=400)

        application = get_object_or_404(MedicalCheckupApplication, id=application_id)
        application.delete()
        return JsonResponse({"status": "success", "message": "Ariza muvaffaqiyatli o'chirildi!"})


@method_decorator(login_required, name='dispatch')
class MedicalCheckupApplicationDetailView(View):
    template_name = 'views/medicalCheckup-detail.html'

    def get(self, request, pk):
        application = get_object_or_404(MedicalCheckupApplication, pk=pk)
        return render(request, self.template_name, {
            "application": application,
            "breadcrumbs": [
                {"title": "Bosh sahifa", "url": reverse('admin-index')},
                {"title": "Tibbiy ko'rik arizalari", "url": reverse('medical-checkup-applications')},
                {"title": application.full_name, "url": "", "active": True},
            ],
        })

    def post(self, request, pk):
        application = get_object_or_404(MedicalCheckupApplication, pk=pk)
        action = request.POST.get("action", "update_status")

        if action == "delete":
            application.delete()
            messages.success(request, "Ariza muvaffaqiyatli o'chirildi.")
            return redirect('medical-checkup-applications')

        status = request.POST.get("status")
        if status not in {"seen", "unseen"}:
            messages.error(request, "Status noto'g'ri yuborildi.")
            return redirect('medical-checkup-application-detail', pk=application.pk)

        application.is_seen = status == "seen"
        application.save(update_fields=["is_seen"])
        messages.success(request, "Ariza statusi yangilandi.")
        return redirect('medical-checkup-application-detail', pk=application.pk)


@method_decorator(login_required, name='dispatch')
class ClinicEquipmentView(View):
    template_name = 'views/clinic_equipment.html'
    paginate_by = 10

    def get_queryset(self, request):
        equipments = ClinicEquipment.objects.all().order_by('-created_at')

        search_query = request.GET.get('q', '').strip()
        if search_query:
            search_filter = Q()
            if search_query.isdigit():
                search_filter |= Q(id=int(search_query))

            for code, _name in settings.LANGUAGES:
                search_filter |= Q(**{f'name__{code}__icontains': search_query})
                search_filter |= Q(**{f'description__{code}__icontains': search_query})

            equipments = equipments.filter(search_filter)

        status_filter = request.GET.get('status', '').strip()
        if status_filter == 'active':
            equipments = equipments.filter(is_active=True)
        elif status_filter == 'inactive':
            equipments = equipments.filter(is_active=False)

        return equipments

    def get_context_data(self, request, form_data=None):
        equipments = self.get_queryset(request)
        paginator = Paginator(equipments, self.paginate_by)
        page_obj = paginator.get_page(request.GET.get('page'))
        search_query = request.GET.get('q', '').strip()
        status_filter = request.GET.get('status', '').strip()
        page_query = {
            key: value
            for key, value in {
                'q': search_query,
                'status': status_filter,
            }.items()
            if value
        }
        all_equipments = ClinicEquipment.objects.all()

        form_data = form_data or {}
        context = {
            'equipments': page_obj,
            'search_query': search_query,
            'status_filter': status_filter,
            'page_query': urlencode(page_query),
            'total_count': all_equipments.count(),
            'active_count': all_equipments.filter(is_active=True).count(),
            'inactive_count': all_equipments.filter(is_active=False).count(),
            'filtered_count': equipments.count(),
            'form_name': form_data.get('name', {}),
            'form_description': form_data.get('description', {}),
            'form_is_active': form_data.get('is_active', True),
            'form_equipment_id': form_data.get('equipment_id', ''),
            'LANGUAGES': settings.LANGUAGES,
            'breadcrumbs': [
                {"title": _("Bosh sahifa"), "url": reverse('admin-index')},
                {"title": _("Tibbiy jihozlar"), "url": reverse('clinic-equipment'), "active": True},
            ],
        }
        return context

    def get(self, request):
        """Qurilmalar ro'yxatini ko'rsatish va yangi qurilma qo'shish formasi."""
        return render(request, self.template_name, self.get_context_data(request))

    def resize_image(self, image_file, width=800, height=600):
        """ Rasmni o‘lchamini o‘zgartirish """
        image = Image.open(image_file)
        image = image.convert('RGBA')
        image = image.resize((width, height), Image.LANCZOS)
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        return InMemoryUploadedFile(buffer, 'ImageField', image_file.name, 'image/png', sys.getsizeof(buffer), None)

    def post(self, request):
        """Yangi qurilma qo'shish, yangilash yoki o'chirish."""
        action = request.POST.get('action', 'save')
        equipment_id = request.POST.get('equipment_id', None)

        if action == 'delete':
            if not equipment_id:
                messages.error(request, "Qurilma ID kiritilmadi.")
                return redirect('clinic-equipment')

            equipment = get_object_or_404(ClinicEquipment, id=equipment_id)
            equipment.delete()
            messages.success(request, "Qurilma muvaffaqiyatli o'chirildi.")
            return redirect('clinic-equipment')

        name = {code: request.POST.get(f'name_{code}', "").strip() for code, name in settings.LANGUAGES}
        description = {code: request.POST.get(f'description_{code}', "").strip() for code, name in settings.LANGUAGES}
        image = request.FILES.get('image')
        is_active = request.POST.get('is_active') == 'on'

        form_data = {
            'equipment_id': equipment_id,
            'name': name,
            'description': description,
            'is_active': is_active,
        }

        if not name.get('uz'):
            messages.error(request, "O'zbek tili uchun qurilma nomi majburiy.")
            return render(request, self.template_name, self.get_context_data(request, form_data=form_data))

        if equipment_id:
            try:
                equipment = ClinicEquipment.objects.get(id=equipment_id)
                equipment.name = name
                equipment.description = description
                if image:
                    equipment.image = self.resize_image(image)
                equipment.is_active = is_active
                equipment.save()
                messages.success(request, "Qurilma muvaffaqiyatli yangilandi.")
            except ClinicEquipment.DoesNotExist:
                messages.error(request, "Qurilma topilmadi.")
                return render(request, self.template_name, self.get_context_data(request, form_data=form_data))
        else:
            equipment = ClinicEquipment(
                name=name,
                description=description,
                image=self.resize_image(image) if image else None,
                is_active=is_active
            )
            equipment.save()
            messages.success(request, "Yangi qurilma muvaffaqiyatli qo'shildi.")

        return redirect('clinic-equipment')

    def delete(self, request, *args, **kwargs):
        """Eski AJAX delete so'rovlari uchun qoldirildi."""
        equipment_id = request.GET.get('equipment_id')
        if not equipment_id:
            return JsonResponse({'success': False, 'message': 'Qurilma ID kiritilmadi.'}, status=400)

        equipment = get_object_or_404(ClinicEquipment, id=equipment_id)
        equipment.delete()
        return JsonResponse({'success': True, 'message': "Qurilma muvaffaqiyatli o'chirildi."})

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'DELETE':
            return self.delete(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

class ClientEquipmentDetailView(DetailView):
    model = ClinicEquipment
    template_name = 'views/client_equipment_detail.html'
    context_object_name = 'equipment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['LANGUAGES'] = settings.LANGUAGES
        context['breadcrumbs'] = [
            {"title": _("Bosh sahifa"), "url": reverse('admin-index')},
            {"title": _("Tibbiy jihozlar"), "url": reverse('clinic-equipment')},
            {"title": self.object.get_name(), "url": "", "active": True},
        ]
        return context

    def post(self, request, *args, **kwargs):
        equipment = self.get_object()
        action = request.POST.get('action', 'save')

        if action == 'delete':
            equipment.delete()
            messages.success(request, "Qurilma muvaffaqiyatli o'chirildi.")
            return redirect('clinic-equipment')

        name = {code: request.POST.get(f'name_{code}', "").strip() for code, name in settings.LANGUAGES}
        description = {code: request.POST.get(f'description_{code}', "").strip() for code, name in settings.LANGUAGES}
        image = request.FILES.get('image')
        is_active = request.POST.get('is_active') == 'on'

        if not name.get('uz'):
            messages.error(request, "O'zbek tili uchun qurilma nomi majburiy.")
            return self.get(request, *args, **kwargs)

        equipment.name = name
        equipment.description = description
        if image:
            # Rasmni o‘lchamini o‘zgartirish
            img = Image.open(image)
            img = img.convert('RGBA')
            img = img.resize((800, 600), Image.LANCZOS)
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            equipment.image = InMemoryUploadedFile(buffer, 'ImageField', image.name, 'image/png', sys.getsizeof(buffer), None)
        equipment.is_active = is_active
        equipment.save()

        messages.success(request, "Qurilma muvaffaqiyatli yangilandi.")
        return redirect('client-equipment-detail', pk=equipment.pk)


@method_decorator(login_required, name='dispatch')
class VideoListView(View):
    template_name = 'views/video_list.html'
    paginate_by = 10

    def get_queryset(self, request):
        videos = Video.objects.all().order_by('-created_at')

        search_query = request.GET.get('q', '').strip()
        if search_query:
            search_filter = Q(embed_url__icontains=search_query)
            for code, _name in settings.LANGUAGES:
                search_filter |= Q(**{f'title__{code}__icontains': search_query})
            videos = videos.filter(search_filter)

        status_filter = request.GET.get('status', '').strip()
        if status_filter == 'active':
            videos = videos.filter(is_active=True)
        elif status_filter == 'inactive':
            videos = videos.filter(is_active=False)

        return videos

    def get_form_state(self, request, form_data=None):
        if form_data is not None:
            return {
                'video_id': form_data.get('video_id', ''),
                'title': form_data.get('title', {}),
                'embed_url': form_data.get('embed_url', ''),
                'is_active': form_data.get('is_active', True),
            }

        edit_video_id = request.GET.get('edit', '').strip()
        if edit_video_id:
            video = Video.objects.filter(id=edit_video_id).first()
            if video:
                return {
                    'video_id': video.id,
                    'title': video.title,
                    'embed_url': video.embed_url,
                    'is_active': video.is_active,
                }

        return {
            'video_id': '',
            'title': {},
            'embed_url': '',
            'is_active': True,
        }

    def get_context_data(self, request, form_data=None):
        videos = self.get_queryset(request)
        paginator = Paginator(videos, self.paginate_by)
        videos_page = paginator.get_page(request.GET.get('page'))
        search_query = request.GET.get('q', '').strip()
        status_filter = request.GET.get('status', '').strip()
        page_query = {
            key: value
            for key, value in {
                'q': search_query,
                'status': status_filter,
            }.items()
            if value
        }
        all_videos = Video.objects.all()
        form_state = self.get_form_state(request, form_data=form_data)

        return {
            'videos': videos_page,
            'search_query': search_query,
            'status_filter': status_filter,
            'page_query': urlencode(page_query),
            'total_count': all_videos.count(),
            'active_count': all_videos.filter(is_active=True).count(),
            'inactive_count': all_videos.filter(is_active=False).count(),
            'filtered_count': videos.count(),
            'form_video_id': form_state['video_id'],
            'form_title': form_state['title'],
            'form_embed_url': form_state['embed_url'],
            'form_is_active': form_state['is_active'],
            'LANGUAGES': settings.LANGUAGES,
            'breadcrumbs': [
                {"title": _("Bosh sahifa"), "url": reverse('admin-index')},
                {"title": _("Videolar ro'yxati"), "url": reverse('video-list'), "active": True},
            ],
        }

    def get(self, request):
        return render(request, self.template_name, self.get_context_data(request))

    def post(self, request):
        action = request.POST.get('action', 'save')
        video_id = request.POST.get('video_id', None)

        if action == 'delete':
            if not video_id:
                messages.error(request, "Video ID kiritilmadi.")
                return redirect('video-list')

            video = get_object_or_404(Video, id=video_id)
            video.delete()
            messages.success(request, "Video muvaffaqiyatli o'chirildi.")
            return redirect('video-list')

        if action == 'update_status':
            if not video_id:
                messages.error(request, "Video ID kiritilmadi.")
                return redirect('video-list')

            video = get_object_or_404(Video, id=video_id)
            status = request.POST.get('status')
            if status not in {'active', 'inactive'}:
                messages.error(request, "Status noto'g'ri yuborildi.")
                return redirect('video-list')

            video.is_active = status == 'active'
            video.save(update_fields=['is_active'])
            messages.success(request, "Video holati yangilandi.")
            return redirect('video-list')

        title = {code: request.POST.get(f'title_{code}', "").strip() for code, name in settings.LANGUAGES}
        embed_url = request.POST.get('embed_url', "").strip()
        is_active = request.POST.get('is_active') == 'on'
        form_data = {
            'video_id': video_id,
            'title': title,
            'embed_url': embed_url,
            'is_active': is_active,
        }

        if not title.get('uz'):
            messages.error(request, "O'zbek tili uchun sarlavha majburiy.")
            return render(request, self.template_name, self.get_context_data(request, form_data=form_data))
        if not embed_url:
            messages.error(request, "YouTube URL yoki Video ID majburiy.")
            return render(request, self.template_name, self.get_context_data(request, form_data=form_data))

        if video_id:
            try:
                video = Video.objects.get(id=video_id)
                video.title = title
                video.embed_url = embed_url
                video.is_active = is_active
                video.save()
                messages.success(request, "Video muvaffaqiyatli yangilandi.")
            except Video.DoesNotExist:
                messages.error(request, "Video topilmadi.")
                return render(request, self.template_name, self.get_context_data(request, form_data=form_data))
            except Exception as exc:
                messages.error(request, f"Xatolik yuz berdi: {exc}")
                return render(request, self.template_name, self.get_context_data(request, form_data=form_data))
        else:
            video = Video(
                title=title,
                embed_url=embed_url,
                is_active=is_active
            )
            try:
                video.full_clean()
                video.save()
                messages.success(request, "Video muvaffaqiyatli qo'shildi.")
            except Exception as exc:
                messages.error(request, f"Xatolik yuz berdi: {exc}")
                return render(request, self.template_name, self.get_context_data(request, form_data=form_data))

        return redirect('video-list')

    def delete(self, request, *args, **kwargs):
        video_id = request.GET.get('video_id')
        if not video_id:
            return JsonResponse({'success': False, 'message': 'Video ID kiritilmadi.'}, status=400)

        video = get_object_or_404(Video, id=video_id)
        video.delete()
        return JsonResponse({'success': True, 'message': "Video muvaffaqiyatli o'chirildi."})

    def patch(self, request, *args, **kwargs):
        video_id = request.GET.get('video_id')
        is_active = request.GET.get('is_active') == 'true'
        if not video_id:
            return JsonResponse({'success': False, 'message': 'Video ID kiritilmadi.'}, status=400)

        video = get_object_or_404(Video, id=video_id)
        video.is_active = is_active
        video.save(update_fields=['is_active'])
        return JsonResponse({'success': True, 'message': 'Holati muvaffaqiyatli yangilandi!'})

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'DELETE':
            return self.delete(request, *args, **kwargs)
        elif request.method == 'PATCH':
            return self.patch(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)


class ClinicServiceFormMixin:
    template_name = "views/service_form.html"

    def get_service_object(self):
        service_id = self.kwargs.get("service_id")
        if not service_id:
            return None
        return get_object_or_404(ClinicService, id=service_id)

    @staticmethod
    def get_back_url(request):
        back_url = request.GET.get("next", "").strip() or request.POST.get("next", "").strip()
        if back_url.startswith("/"):
            return back_url
        return reverse("service-list")

    @staticmethod
    def parse_sort_order(value):
        try:
            return max(0, int((value or "").strip() or 0))
        except (TypeError, ValueError, AttributeError):
            return 0

    def get_initial_form_data(self, service=None):
        return {
            "title": service.title if service else {},
            "summary": service.summary if service else {},
            "icon_class": service.icon_class if service else "flaticon-medicine",
            "sort_order": service.sort_order if service else 0,
            "is_active": service.is_active if service else True,
        }

    def get_form_data(self, request):
        allowed_icons = {choice[0] for choice in FLATICON_ICON_CHOICES}
        icon_class = request.POST.get("icon_class", "flaticon-medicine").strip()
        if icon_class not in allowed_icons:
            icon_class = "flaticon-medicine"

        return {
            "title": {
                code: request.POST.get(f"title_{code}", "").strip()
                for code, _name in settings.LANGUAGES
            },
            "summary": {
                code: CustomUser.normalize_rich_text_content(request.POST.get(f"summary_{code}", ""))
                for code, _name in settings.LANGUAGES
            },
            "icon_class": icon_class,
            "sort_order": self.parse_sort_order(request.POST.get("sort_order", "0")),
            "is_active": request.POST.get("is_active") == "on",
        }

    @staticmethod
    def validate_form_data(form_data):
        errors = []
        if not form_data["title"].get("uz"):
            errors.append("O'zbek tili uchun xizmat nomi majburiy.")
        return errors

    @staticmethod
    def clean_multilingual_payload(payload):
        return {
            code: value
            for code, value in payload.items()
            if (value or "").strip()
        }

    def apply_form_data(self, service, form_data):
        service.title = self.clean_multilingual_payload(form_data["title"])
        service.summary = self.clean_multilingual_payload(form_data["summary"])
        service.icon_class = form_data["icon_class"]
        service.sort_order = form_data["sort_order"]
        service.is_active = form_data["is_active"]
        return service

    def get_context_data(self, request, service=None, form_data=None):
        if form_data is None:
            form_data = self.get_initial_form_data(service=service)

        is_edit = service is not None
        page_title = "Xizmatni tahrirlash" if is_edit else "Xizmat qo'shish"
        page_subtitle = (
            "Landing sahifadagi xizmat ma'lumotlari, ikonka va tartibini yangilang."
            if is_edit
            else "Yangi xizmat uchun nom, tavsif, ikonka va tartib ma'lumotlarini kiriting."
        )
        back_url = self.get_back_url(request)
        selected_icon_label = next(
            (str(label) for value, label in FLATICON_ICON_CHOICES if value == form_data["icon_class"]),
            form_data["icon_class"],
        )

        return {
            "service": service,
            "form_title": form_data["title"],
            "form_summary": form_data["summary"],
            "form_icon_class": form_data["icon_class"],
            "selected_icon_label": selected_icon_label,
            "form_sort_order": form_data["sort_order"],
            "form_is_active": form_data["is_active"],
            "icon_choices": FLATICON_ICON_CHOICES,
            "LANGUAGES": settings.LANGUAGES,
            "page_title": page_title,
            "page_subtitle": page_subtitle,
            "submit_label": "Saqlash" if is_edit else "Qo'shish",
            "form_action_url": (
                reverse("service-edit", kwargs={"service_id": service.id})
                if is_edit
                else reverse("service-create")
            ),
            "back_url": back_url,
            "breadcrumbs": [
                {"title": "Bosh sahifa", "url": reverse("admin-index")},
                {"title": "Xizmatlar", "url": reverse("service-list")},
                {
                    "title": page_title,
                    "url": (
                        reverse("service-edit", kwargs={"service_id": service.id})
                        if is_edit
                        else reverse("service-create")
                    ),
                    "active": True,
                },
            ],
        }


@method_decorator(login_required, name="dispatch")
class ServiceListView(View):
    template_name = "views/service_list.html"
    paginate_by = 12

    def get_queryset(self, request):
        services = ClinicService.objects.all().order_by("sort_order", "id")
        search_query = request.GET.get("q", "").strip()
        status_filter = request.GET.get("status", "").strip()

        if search_query:
            search_filter = Q(icon_class__icontains=search_query)
            if search_query.isdigit():
                search_filter |= Q(id=int(search_query))
                search_filter |= Q(sort_order=int(search_query))

            for code, _name in settings.LANGUAGES:
                search_filter |= Q(**{f"title__{code}__icontains": search_query})
                search_filter |= Q(**{f"summary__{code}__icontains": search_query})

            services = services.filter(search_filter)

        if status_filter == "active":
            services = services.filter(is_active=True)
        elif status_filter == "inactive":
            services = services.filter(is_active=False)

        return services

    def get_context_data(self, request):
        services_queryset = self.get_queryset(request)
        paginator = Paginator(services_queryset, self.paginate_by)
        services = paginator.get_page(request.GET.get("page"))
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
        all_services = ClinicService.objects.all()

        return {
            "services": services,
            "search_query": search_query,
            "status_filter": status_filter,
            "page_query": urlencode(page_query),
            "current_path": request.get_full_path(),
            "total_count": all_services.count(),
            "active_count": all_services.filter(is_active=True).count(),
            "inactive_count": all_services.filter(is_active=False).count(),
            "filtered_count": services_queryset.count(),
            "breadcrumbs": [
                {"title": "Bosh sahifa", "url": reverse("admin-index")},
                {"title": "Xizmatlar", "url": reverse("service-list"), "active": True},
            ],
        }

    @staticmethod
    def redirect_to_list(request):
        return_path = request.POST.get("return_path", "").strip()
        if return_path.startswith("/"):
            return redirect(return_path)
        return redirect("service-list")

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data(request))

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action", "").strip()
        service_id = request.POST.get("service_id", "").strip()

        if not service_id:
            messages.error(request, "Xizmat ID topilmadi.")
            return self.redirect_to_list(request)

        service = get_object_or_404(ClinicService, id=service_id)
        service_name = service.get_title("uz")

        if action == "delete":
            service.delete()
            messages.success(request, f"{service_name} muvaffaqiyatli o'chirildi.")
            return self.redirect_to_list(request)

        if action == "update_status":
            status = request.POST.get("status", "").strip()
            if status not in {"active", "inactive"}:
                messages.error(request, "Status noto'g'ri yuborildi.")
                return self.redirect_to_list(request)

            service.is_active = status == "active"
            service.save(update_fields=["is_active"])
            messages.success(request, "Xizmat holati yangilandi.")
            return self.redirect_to_list(request)

        messages.error(request, "Noto'g'ri amal yuborildi.")
        return self.redirect_to_list(request)


@method_decorator(login_required, name="dispatch")
class ServiceCreateView(ClinicServiceFormMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data(request))

    def post(self, request, *args, **kwargs):
        form_data = self.get_form_data(request)
        errors = self.validate_form_data(form_data)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, self.template_name, self.get_context_data(request, form_data=form_data))

        try:
            service = self.apply_form_data(ClinicService(), form_data)
            service.save()
            messages.success(request, f"{service.get_title('uz')} muvaffaqiyatli qo'shildi.")
            return redirect(self.get_back_url(request))
        except Exception as exc:
            messages.error(request, f"Xizmatni saqlashda xatolik yuz berdi: {exc}")
            return render(request, self.template_name, self.get_context_data(request, form_data=form_data))


@method_decorator(login_required, name="dispatch")
class ServiceEditView(ClinicServiceFormMixin, View):
    def get(self, request, service_id, *args, **kwargs):
        service = self.get_service_object()
        return render(request, self.template_name, self.get_context_data(request, service=service))

    def post(self, request, service_id, *args, **kwargs):
        service = self.get_service_object()
        form_data = self.get_form_data(request)
        errors = self.validate_form_data(form_data)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, self.template_name, self.get_context_data(request, service=service, form_data=form_data))

        try:
            self.apply_form_data(service, form_data)
            service.save()
            messages.success(request, f"{service.get_title('uz')} muvaffaqiyatli tahrirlandi.")
            return redirect(self.get_back_url(request))
        except Exception as exc:
            messages.error(request, f"Xizmatni tahrirlashda xatolik yuz berdi: {exc}")
            return render(request, self.template_name, self.get_context_data(request, service=service, form_data=form_data))
