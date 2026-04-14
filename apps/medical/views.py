import json
from datetime import datetime
import traceback
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
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
from urllib.parse import urlparse
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from config import settings
from config.settings import LANGUAGES
from config.telegram_bot import send_message
from members.models import CustomUser, Appointment
from .forms import VideoForm
from .models import SiteSettings, MainPageBanner, DoctorAInfo, ContactPhone, Partner, MedicalCheckupApplication, \
    ClinicEquipment, Video


class MainView(TemplateView):
    template_name = 'views/main.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.objects.first()
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
            print("🎥 Video 1 yuklandi.")
        if 'video2' in request.FILES:
            site_settings.video2 = request.FILES['video2']
            print("🎥 Video 2 yuklandi.")

        site_settings.save()

        # Banner uchun
        image = request.FILES.get('banner_image')
        description = {
            code: self.normalize_rich_text(request.POST.get(f'description_{code}', ""))
            for code, name in settings.LANGUAGES
        }

        print(f"🟢 So‘rov qabul qilindi! image={'bor' if image else 'yo‘q'}")

        missing_fields = []
        if not description.get('uz'):
            missing_fields.append("📌 O'zbek tili uchun tavsif majburiy.")

        if missing_fields:
            print("❌ Xatoliklar:", missing_fields)
            messages.error(request, " ".join(missing_fields))
            context = self.get_context_data()
            return render(request, self.template_name, context)

        banner = MainPageBanner.objects.first()

        if not banner and not image:
            messages.error(request, "📌 Banner rasmi majburiy.")
            context = self.get_context_data()
            return render(request, self.template_name, context)

        if banner:
            print(f"✏️ Banner yangilanmoqda... ID: {banner.id}")
            banner.description = description
            if image:
                banner.image = image
                print("📸 Yangi rasm yuklandi.")
            banner.save()
            print("✅ Banner yangilandi!")
        else:
            print("🆕 Yangi banner qo‘shilmoqda...")
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
class PartnerInfoView(TemplateView):
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

@method_decorator(login_required, name='dispatch')
class RolesView(TemplateView):
    template_name = 'havfsizlik/roles.html'

    def get_context_data(self, **kwargs):
        """ Sahifa uchun kontekst ma'lumotlari """
        context = super().get_context_data(**kwargs)

        return context


@method_decorator(login_required, name='dispatch')
class LogsView(TemplateView):
    template_name = 'havfsizlik/logs.html'

    def get_context_data(self, **kwargs):
        """ Sahifa uchun kontekst ma'lumotlari """
        context = super().get_context_data(**kwargs)

        return context


@method_decorator(login_required, name='dispatch')
class AppointmentView(View):
    template_name = 'views/appointment.html'
    paginate_by = 10  # Har bir sahifada 10 ta qabul chiqadi

    def get(self, request):
        """ Qabul ro‘yxatini chiqarish (qidirish + pagination) """
        appointments = Appointment.objects.all().order_by('-created_at')



        # ✅ **Pagination**
        paginator = Paginator(appointments.order_by('-created_at'), self.paginate_by)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Breadcrumb uchun kontekst
        breadcrumbs = [
            {"title": "Bosh sahifa", "url": reverse('admin-index')},
            {"title": "Qabullar", "url": reverse('appointment-view'), "active": True},
        ]

        return render(request, self.template_name, {
            "appointments": page_obj,
            "breadcrumbs": breadcrumbs,  # Breadcrumb qo‘shildi
        })

    def post(self, request):
        """ Qabul holatini o‘zgartirish """
        appointment_id = request.POST.get('appointment_id')
        status = request.POST.get('status')

        if appointment_id and status in ['pending', 'approved', 'canceled']:
            appointment = get_object_or_404(Appointment, id=appointment_id)
            appointment.status = status
            appointment.save()
            return JsonResponse({"success": True, "message": "✅ Qabul holati yangilandi!"})

        return JsonResponse({"success": False, "message": "❌ Xato so‘rov!"}, status=400)

    def delete(self, request):
        """ Qabulni o‘chirish """
        appointment_id = request.GET.get('appointment_id')
        appointment = get_object_or_404(Appointment, id=appointment_id)
        appointment.delete()
        return JsonResponse({"success": True, "message": "✅ Qabul o‘chirildi!"})

@method_decorator(login_required, name='dispatch')
class MedicalCheckupApplicationView(View):
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
class ClinicEquipmentView(View):
    template_name = 'views/clinic_equipment.html'

    def get(self, request):
        """ Qurilmalar ro‘yxatini ko‘rsatish va yangi qurilma qo‘shish formasi """
        equipments = ClinicEquipment.objects.all()

        # Breadcrumb uchun kontekst
        breadcrumbs = [
            {"title": _("Bosh sahifa"), "url": reverse('admin-index')},
            {"title": _("Tibbiy jihozlar"), "url": reverse('clinic-equipment'), "active": True},
        ]

        context = {
            'equipments': equipments,
            'LANGUAGES': settings.LANGUAGES,
            'breadcrumbs': breadcrumbs,  # Breadcrumb'ni qo‘shdik
        }
        return render(request, self.template_name, context)

    def resize_image(self, image_file, width=800, height=600):
        """ Rasmni o‘lchamini o‘zgartirish """
        image = Image.open(image_file)
        image = image.convert('RGBA')
        image = image.resize((width, height), Image.LANCZOS)
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        return InMemoryUploadedFile(buffer, 'ImageField', image_file.name, 'image/png', sys.getsizeof(buffer), None)

    def post(self, request):
        """ Yangi qurilma qo‘shish yoki mavjud qurilmani yangilash """
        equipment_id = request.POST.get('equipment_id', None)  # Agar ID bo‘lsa, yangilash uchun
        name = {code: request.POST.get(f'name_{code}', "").strip() for code, name in settings.LANGUAGES}
        description = {code: request.POST.get(f'description_{code}', "").strip() for code, name in settings.LANGUAGES}
        image = request.FILES.get('image')
        is_active = request.POST.get('is_active') == 'on'

        # O‘zbek tili majburiy
        if not name.get('uz'):
            messages.error(request, "📌 O‘zbek tili uchun qurilma nomi majburiy.")
            context = self.get_context_data()
            context['equipments'] = ClinicEquipment.objects.all()
            return render(request, self.template_name, context)

        if equipment_id:  # Yangilash
            try:
                equipment = ClinicEquipment.objects.get(id=equipment_id)
                equipment.name = name
                equipment.description = description
                if image:
                    equipment.image = self.resize_image(image)
                equipment.is_active = is_active
                equipment.save()
                messages.success(request, "✅ Qurilma muvaffaqiyatli yangilandi!")
            except ClinicEquipment.DoesNotExist:
                messages.error(request, "❌ Qurilma topilmadi!")
        else:  # Yangi qurilma qo‘shish
            equipment = ClinicEquipment(
                name=name,
                description=description,
                image=self.resize_image(image) if image else None,
                is_active=is_active
            )
            equipment.save()
            messages.success(request, "✅ Yangi qurilma muvaffaqiyatli qo‘shildi!")

        return redirect('clinic-equipment')

    def delete(self, request, *args, **kwargs):
        """ Qurilmani o‘chirish """
        equipment_id = request.GET.get('equipment_id')
        try:
            equipment = ClinicEquipment.objects.get(id=equipment_id)
            equipment.delete()
            return JsonResponse({'success': True, 'message': 'Qurilma muvaffaqiyatli o‘chirildi!'})
        except ClinicEquipment.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Qurilma topilmadi!'}, status=404)

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
        return context

    def post(self, request, *args, **kwargs):
        equipment = self.get_object()
        name = {code: request.POST.get(f'name_{code}', "").strip() for code, name in settings.LANGUAGES}
        description = {code: request.POST.get(f'description_{code}', "").strip() for code, name in settings.LANGUAGES}
        image = request.FILES.get('image')
        is_active = request.POST.get('is_active') == 'on'

        if not name.get('uz'):
            messages.error(request, "📌 O‘zbek tili uchun qurilma nomi majburiy.")
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

        messages.success(request, "✅ Qurilma muvaffaqiyatli yangilandi!")
        return redirect('client-equipment-detail', pk=equipment.pk)


@method_decorator(login_required, name='dispatch')
class VideoListView(View):
    template_name = 'views/video_list.html'

    def get(self, request):
        search_query = request.GET.get('q', '').strip()
        videos = Video.objects.all()

        if search_query:
            videos = videos.filter(
                Q(title__uz__icontains=search_query) |
                Q(embed_url__icontains=search_query)
            )

        paginator = Paginator(videos, 5)
        page_number = request.GET.get('page')
        videos_page = paginator.get_page(page_number)

        # Breadcrumb uchun kontekst
        breadcrumbs = [
            {"title": _("Bosh sahifa"), "url": reverse('admin-index')},
            {"title": _("Videolar ro‘yxati"), "url": reverse('video-list'), "active": True},
        ]

        context = {
            'videos': videos_page,
            'search_query': search_query,
            'LANGUAGES': settings.LANGUAGES,
            'breadcrumbs': breadcrumbs,  # Breadcrumb'ni context'ga qo‘shdik
        }
        return render(request, self.template_name, context)

    def post(self, request):
        video_id = request.POST.get('video_id', None)
        title = {code: request.POST.get(f'title_{code}', "").strip() for code, name in settings.LANGUAGES}
        embed_url = request.POST.get('embed_url', "").strip()
        is_active = request.POST.get('is_active') == 'on'

        if not title.get('uz'):
            messages.error(request, "📌 O‘zbek tili uchun sarlavha majburiy.")
            return self.get(request)
        if not embed_url:
            messages.error(request, "📌 YouTube URL yoki Video ID majburiy.")
            return self.get(request)

        if video_id:  # Tahrirlash
            try:
                video = Video.objects.get(id=video_id)
                video.title = title
                video.embed_url = embed_url
                video.is_active = is_active
                video.save()
                messages.success(request, "✅ Video muvaffaqiyatli yangilandi!")
            except Video.DoesNotExist:
                messages.error(request, "❌ Video topilmadi!")
        else:  # Yangi video qo‘shish
            video = Video(
                title=title,
                embed_url=embed_url,
                is_active=is_active
            )
            try:
                video.full_clean()
                video.save()
                messages.success(request, "✅ Video muvaffaqiyatli qo‘shildi!")
            except Exception as e:
                messages.error(request, f"📌 Xatolik yuz berdi: {str(e)}")
                return self.get(request)

        return redirect('video-list')

    def delete(self, request, *args, **kwargs):
        video_id = request.GET.get('video_id')
        try:
            video = Video.objects.get(id=video_id)
            video.delete()
            return JsonResponse({'success': True, 'message': 'Video muvaffaqiyatli o‘chirildi!'})
        except Video.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Video topilmadi!'}, status=404)

    def patch(self, request, *args, **kwargs):
        video_id = request.GET.get('video_id')
        is_active = request.GET.get('is_active') == 'true'
        try:
            video = Video.objects.get(id=video_id)
            video.is_active = is_active
            video.save()
            return JsonResponse({'success': True, 'message': 'Holati muvaffaqiyatli yangilandi!'})
        except Video.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Video topilmadi!'}, status=404)

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'DELETE':
            return self.delete(request, *args, **kwargs)
        elif request.method == 'PATCH':
            return self.patch(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)
