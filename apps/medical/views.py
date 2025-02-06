import json

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from PIL import Image
from django.utils.translation import gettext_lazy as _
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

from config import settings
from config.settings import LANGUAGES
from members.models import CustomUser
from .models import SiteSettings, MainPageBanner, DoctorAInfo, ContactPhone


class MainView(TemplateView):
    template_name = 'views/main.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.objects.first()
        return context

    def resize_image(self, image_file, width=136, height=40):
        image = Image.open(image_file)
        image = image.convert('RGBA')
        image = image.resize((width, height), Image.LANCZOS)
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        return InMemoryUploadedFile(buffer, 'ImageField', image_file.name, 'image/png', sys.getsizeof(buffer), None)

    def post(self, request, *args, **kwargs):
        site_settings = SiteSettings.objects.first()
        if not site_settings:
            site_settings = SiteSettings()

        site_settings.site_name = request.POST.get('site_name', site_settings.site_name)
        site_settings.contact_email = request.POST.get('contact_email', site_settings.contact_email)
        site_settings.contact_phone = request.POST.get('contact_phone', site_settings.contact_phone)
        site_settings.address = request.POST.get('address', site_settings.address)
        site_settings.maintenance_mode = request.POST.get('maintenance_mode') == 'on'

        if 'logo_dark' in request.FILES:
            site_settings.logo_dark = self.resize_image(request.FILES['logo_dark'])
        if 'logo_light' in request.FILES:
            site_settings.logo_light = self.resize_image(request.FILES['logo_light'])

        site_settings.save()
        messages.success(request, "Sayt sozlamalari muvaffaqiyatli saqlandi!")
        return redirect('admin-index')


class MainPageBannerView(TemplateView):
    template_name = 'views/main-page-banner.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['banners'] = MainPageBanner.objects.all()
        context['LANGUAGES'] = LANGUAGES
        return context

    def post(self, request, *args, **kwargs):
        """ Bannerni qo‘shish yoki yangilash """

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # AJAX so‘rovi tekshiriladi
            banner_id = request.POST.get('banner_id')
            image = request.FILES.get('banner_image')  # Yangi yuklangan rasm
            description = {code: request.POST.get(f'description[{code}]', "").strip() for code, name in LANGUAGES}

            print(f"🟢 So‘rov qabul qilindi! banner_id={banner_id}, image={'bor' if image else 'yo‘q'}")

            # Xatoliklarni tekshirish
            missing_fields = []

            if not banner_id and not image:
                missing_fields.append("📌 Banner rasmi yuklanmagan.")

            if not description.get('uz'):
                missing_fields.append("📌 O'zbek tili uchun tavsif majburiy.")

            for code, name in LANGUAGES:
                if not description[code]:
                    missing_fields.append(f"📌 {name} tili uchun tavsif kiritilmagan.")

            if missing_fields:
                print("❌ Xatoliklar ro‘yxati:", missing_fields)
                return JsonResponse({"success": False, "error": "<br>".join(missing_fields)}, status=400)

            # **Tahrirlash yoki yangi banner qo‘shish**
            if banner_id:  # **Tahrirlash**
                banner = MainPageBanner.objects.filter(id=banner_id).first()

                if not banner:
                    print(f"❌ Xatolik: Banner ID {banner_id} topilmadi!")
                    return JsonResponse({"success": False, "error": "❌ Bunday banner topilmadi!"}, status=404)

                print(f"✏️ Tahrirlash: Banner ID {banner_id} topildi, yangilanmoqda...")

                banner.description = description
                if image:  # **Yangi rasm bo‘lsa, almashtirish**
                    print("📸 Yangi rasm yuklandi, almashtirildi.")
                    banner.image = image

                banner.save()
                print("✅ Banner muvaffaqiyatli yangilandi!")
                return JsonResponse({"success": True, "message": "✅ Banner muvaffaqiyatli yangilandi!"})

            else:  # **Yangi banner qo‘shish**
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
class DoctorAInfoView(TemplateView):
    template_name = 'views/doctor_a.html'

    def get_context_data(self, **kwargs):
        """ Sahifa uchun kontekst ma'lumotlari """
        context = super().get_context_data(**kwargs)
        doctor_id = self.request.GET.get("doctor_id")

        if doctor_id:
            context["doctor_info"] = DoctorAInfo.objects.filter(id=doctor_id).first()
        else:
            context["doctor_info_list"] = DoctorAInfo.objects.all()  # Barcha ma'lumotlarni olish

        context["LANGUAGES"] = settings.LANGUAGES  # Tilni HTML-ga uzatish
        context["LANGUAGES_JSON"] = json.dumps([(code, str(name)) for code, name in settings.LANGUAGES])

        return context

    def post(self, request):
        """ Yangi Doctor A ma'lumotini qo‘shish yoki mavjudini yangilash """
        doctor_id = request.POST.get("doctor_id")
        image = request.FILES.get("image")
        title = {code: request.POST.get(f'title[{code}]', "").strip() for code, _ in settings.LANGUAGES}
        description = {code: request.POST.get(f'description[{code}]', "").strip() for code, _ in settings.LANGUAGES}

        errors = []
        if not title.get("uz"):
            errors.append("📌 O'zbek tilida sarlavha kiritish majburiy.")
        if not description.get("uz"):
            errors.append("📌 O'zbek tilida tavsif kiritish majburiy.")
        if not doctor_id and not image:
            errors.append("📌 Rasm yuklash majburiy.")

        if errors:
            return JsonResponse({"success": False, "error": "<br>".join(errors)}, status=400)

        # **Tahrirlash yoki yangi ma'lumot qo‘shish**
        if doctor_id:  # **Tahrirlash**
            doctor = get_object_or_404(DoctorAInfo, id=doctor_id)
            doctor.title = title
            doctor.description = description
            if image:
                doctor.image = image  # Yangi rasm yuklangan bo‘lsa, almashtirish
            doctor.save()
            return JsonResponse({"success": True, "message": "✅ Doctor A ma'lumotlari yangilandi!"})

        else:  # **Yangi qo‘shish**
            doctor = DoctorAInfo.objects.create(title=title, description=description, image=image)
            return JsonResponse({"success": True, "message": "✅ Doctor A ma'lumotlari qo‘shildi!"})

    def patch(self, request):
        """ Ma'lumotni tahrirlash (rasmni ham yangilash) """
        print("🟡 PATCH so‘rovi kelib tushdi.")

        try:
            doctor_id = request.POST.get("doctor_id")
            title = json.loads(request.POST.get("title", "{}"))
            description = json.loads(request.POST.get("description", "{}"))
            image = request.FILES.get("image")  # 🔹 Rasmni olish

            print(f"📌 Olingan doctor_id: {doctor_id}")
            print("📖 Title ma'lumotlari:", title)
            print("📖 Description ma'lumotlari:", description)
            print("📷 Yuklangan rasm:", image)

            if not doctor_id:
                print("🔴 Xatolik: doctor_id kiritilmagan!")
                return JsonResponse({"success": False, "error": "❌ ID kiritilishi shart!"}, status=400)

            doctor = get_object_or_404(DoctorAInfo, id=doctor_id)
            print(f"🟢 Doctor ma'lumotlari topildi: {doctor}")

            # 🔹 Yangilash
            doctor.title = title
            doctor.description = description
            if image:
                doctor.image = image  # 🔹 Agar rasm yuklangan bo‘lsa, yangilash
                print("🖼️ Rasm yangilandi!")

            doctor.save()
            print("✅ Doctor A ma'lumotlari yangilandi!")

            return JsonResponse({"success": True, "message": "✅ Doctor A ma'lumotlari yangilandi!"})

        except json.JSONDecodeError:
            print("🔴 Xatolik: JSON formati noto‘g‘ri!")
            return JsonResponse({"success": False, "error": "❌ Noto‘g‘ri JSON formati!"}, status=400)

    def delete(self, request):
        """ Ma'lumotni o‘chirish """
        try:
            data = json.loads(request.body)
            doctor_id = data.get("doctor_id")

            if not doctor_id:
                print("🔴 Xatolik: ID kiritilmagan!")
                return JsonResponse({"success": False, "error": "❌ ID kiritilishi shart!"}, status=400)

            doctor = get_object_or_404(DoctorAInfo, id=doctor_id)
            doctor.delete()
            print(f"🟢 Doctor ID={doctor_id} muvaffaqiyatli o‘chirildi!")

            return JsonResponse({"success": True, "message": "✅ Doctor A ma'lumotlari o‘chirildi!"})

        except json.JSONDecodeError:
            print("🔴 Xatolik: JSON formati noto‘g‘ri!")
            return JsonResponse({"success": False, "error": "❌ Noto‘g‘ri JSON formati!"}, status=400)


@login_required
@csrf_exempt  # CSRF muammolarni oldini olish uchun
def get_doctor_info(request):
    """ AJAX orqali Doctor A ma'lumotlarini olish """
    if request.method != "GET":
        return JsonResponse({"error": "❌ Faqat GET so‘rovlarga ruxsat berilgan!"}, status=405)

    doctor_id = request.GET.get("doctor_id")
    if not doctor_id:
        return JsonResponse({"error": "❌ Doctor ID ko‘rsatilishi shart!"}, status=400)

    # Doctor ma'lumotini olish yoki 404 qaytarish
    doctor = get_object_or_404(DoctorAInfo, id=doctor_id)

    data = {
        "id": doctor.id,
        "image_url": doctor.image.url if doctor.image else "",
        "title": doctor.title,  # JSON formatda
        "description": doctor.description  # JSON formatda
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
class UsersView(TemplateView):
    template_name = 'havfsizlik/users.html'

    def get_context_data(self, **kwargs):
        """ Foydalanuvchilar uchun context yaratish """
        context = super().get_context_data(**kwargs)
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

        context["users"] = paginated_users
        context["search_query"] = search_query
        context["LANGUAGES"] = settings.LANGUAGES
        context["total_pages"] = paginator.num_pages
        context["current_page"] = paginated_users.number
        context["has_next"] = paginated_users.has_next()
        context["has_previous"] = paginated_users.has_previous()
        return context


@method_decorator(login_required, name='dispatch')
class AddUsersView(TemplateView):
    template_name = 'havfsizlik/add-users.html'

    def get_context_data(self, **kwargs):
        """ Foydalanuvchilar uchun context yaratish """
        context = super().get_context_data(**kwargs)

        return context






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
