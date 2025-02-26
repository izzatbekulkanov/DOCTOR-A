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
from config.telegram_bot import send_message
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
            banner, created = MainPageBanner.objects.get_or_create(id=1, defaults={"description": description,
                                                                                   "image": image})

            if not created:  # **Agar mavjud bo‘lsa, uni yangilaymiz**
                print(f"✏️ Mavjud banner yangilanmoqda... ID: {banner.id}")
                banner.description = description
                if image:  # **Agar yangi rasm bo‘lsa, uni almashtiramiz**
                    print("📸 Yangi rasm yuklandi, almashtirildi.")
                    banner.image = image
                banner.save()
                print("✅ Banner muvaffaqiyatli yangilandi!")
                return JsonResponse({"success": True, "message": "✅ Banner muvaffaqiyatli yangilandi!"})

            print(f"✅ Yangi banner yaratildi! ID: {banner.id}")
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
class AddUsersView(View):
    template_name = 'havfsizlik/add-users.html'

    def get(self, request, *args, **kwargs):
        """ GET so‘rovni qabul qiladi va sahifani qaytaradi """
        print("\n📌 DEBUG: GET so‘rovi kelib tushdi!")
        print(f"🌍 URL: {request.build_absolute_uri()}")
        print(f"🔍 GET Parametrlari: {dict(request.GET)}")
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        """ POST so‘rov bilan foydalanuvchini yaratish """

        # ✅ So‘rov turini aniqlab, debugging uchun chiqarish
        print("\n📌 DEBUG: POST so‘rovi qabul qilindi!")
        print(f"🌍 URL: {request.build_absolute_uri()}")
        print(f"📨 So‘rov turi: {request.method}")

        # ✅ Yuborilgan `POST` ma’lumotlarini chiqarish
        print("📩 Yuborilgan POST ma’lumotlari:")
        for key, value in request.POST.items():
            print(f"  - {key}: {value}")

        # ✅ Agar `FILES` mavjud bo‘lsa, chiqaramiz
        if request.FILES:
            print("🖼 Yuklangan fayllar:")
            for key, file in request.FILES.items():
                print(f"  - {key}: {file.name} ({file.content_type})")

        # ✅ Majburiy maydonlarni olish
        full_name = request.POST.get("full_name")
        phone_number = request.POST.get("phone_number")
        gender = request.POST.get("gender")
        username = request.POST.get("username")
        address = request.POST.get("address")
        emergency_contact = request.POST.get("emergency_contact")
        employment_date = request.POST.get("employment_date")
        employee_id = request.POST.get("employee_id")
        bio = request.POST.get("bio")
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

        profile_picture = request.FILES.get("profile_picture")  # Agar rasm yuklangan bo‘lsa

        # ✅ Majburiy maydonlarni tekshirish
        if not full_name:
            print("❌ Xatolik: Majburiy maydonlar to‘ldirilmagan!")
            return JsonResponse({"status": "error", "message": "Majburiy maydonlarni to‘ldiring!"}, status=400)

        # ✅ Foydalanuvchi yaratish
        print("🚀 Yangi foydalanuvchi yaratish jarayoni boshlandi...")
        user = CustomUser(
            full_name=full_name,
            username=username,
            address=address,
            emergency_contact=emergency_contact,
            insurance_number=insurance_number,
            shift_schedule=shift_schedule,
            employment_date=employment_date,
            tax_identification_number=tax_identification_number,
            medical_specialty=medical_specialty,
            bank_account_number=bank_account_number,
            contract_end_date=contract_end_date,
            professional_license_number=professional_license_number,
            department=department,
            bio=bio,
            nationality=nationality,
            employee_id=employee_id,
            phone_number=phone_number,
            gender=gender,
            date_of_birth=date_of_birth,
            job_title=job_title,
            is_active=is_active,
            profile_picture=profile_picture
        )

        # ✅ Telegram kanaliga xabar yuborish
        message_text = (
            f"👤 <b>Yangi foydalanuvchi qo‘shildi!</b>\n"
            f"#_<b>ADD_USER</b>\n"
            f"📌 Ismi: {full_name}\n"
            f"📛 Foydalanuvchi nomi: {username}\n"
            f"📞 Telefon: {phone_number}\n"
            f"🏠 Manzil: {address}\n"
            f"🎂 Tug‘ilgan sana: {date_of_birth}\n"
            f"⚥ Jinsi: {'Erkak' if gender == 'male' else 'Ayol'}\n"
            f"🌍 Millati: {nationality}\n"
            f"🆔 Xodim ID: {employee_id}\n"
            f"📝 Bio: {bio}\n"
            f"🚑 Favqulodda aloqa: {emergency_contact}\n"
            f"🏢 Bo‘lim: {department}\n"
            f"💼 Lavozim: {job_title}\n"
            f"📅 Ishga kirgan sana: {employment_date}\n"
            f"📆 Shartnoma muddati: {contract_end_date}\n"
            f"🔢 Professional litsenziya raqami: {professional_license_number}\n"
            f"🩺 Tibbiy mutaxassisligi: {medical_specialty}\n"
            f"⏰ Ish jadvali: {shift_schedule}\n"
            f"🏦 Bank hisobi: {bank_account_number}\n"
            f"🆔 Soliq identifikatsiya raqami: {tax_identification_number}\n"
            f"🛡 Sug‘urta raqami: {insurance_number}\n"
            f"🟢 Holati: {'Faol' if is_active == 'True' else 'Faol emas'}"
        )

        send_message(message_text)

        user.save()

        print(f"✅ Foydalanuvchi qo‘shildi: {user.full_name} (ID: {user.id})")
        return JsonResponse({"status": "success", "message": "Foydalanuvchi muvaffaqiyatli qo‘shildi!"})


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
