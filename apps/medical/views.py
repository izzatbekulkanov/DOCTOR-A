import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from PIL import Image
from django.utils.translation import gettext_lazy as _
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

from config.settings import LANGUAGES
from .models import SiteSettings, MainPageBanner, DoctorAInfo


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


class DoctorAInfoView(TemplateView):
    template_name = 'views/doctor_a.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor_id = self.request.GET.get("doctor_id")

        if doctor_id:
            context["doctor_info"] = DoctorAInfo.objects.filter(id=doctor_id).first()
        else:
            context["doctor_info_list"] = DoctorAInfo.objects.all()  # Barcha ma'lumotlarni olish

        context["LANGUAGES"] = LANGUAGES  # Tilni HTML-ga uzatish
        return context

    def post(self, request):
        """ Yangi Doctor A ma'lumotini qo‘shish yoki yangilash """
        doctor_id = request.POST.get("doctor_id")
        image = request.FILES.get("image")
        title = {code: request.POST.get(f'title[{code}]', "").strip() for code, name in LANGUAGES}
        description = {code: request.POST.get(f'description[{code}]', "").strip() for code, name in LANGUAGES}

        # Xatoliklarni tekshirish
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
            try:
                doctor = DoctorAInfo.objects.get(id=doctor_id)
            except DoctorAInfo.DoesNotExist:
                return JsonResponse({"success": False, "error": "❌ Bunday ma'lumot topilmadi!"}, status=404)

            doctor.title = title
            doctor.description = description
            if image:
                doctor.image = image  # Yangi rasm yuklangan bo‘lsa, almashtirish
            doctor.save()
            return JsonResponse({"success": True, "message": "✅ Doctor A ma'lumotlari yangilandi!"})

        else:  # **Yangi qo‘shish**
            doctor = DoctorAInfo.objects.create(title=title, description=description, image=image)
            return JsonResponse({"success": True, "message": "✅ Doctor A ma'lumotlari qo‘shildi!"})

    def delete(self, request):
        """ Ma'lumotni o‘chirish """
        try:
            body = json.loads(request.body)
            doctor_id = body.get("doctor_id")
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "❌ Noto‘g‘ri ma'lumot formati!"}, status=400)

        if not doctor_id:
            return JsonResponse({"success": False, "error": "❌ ID kiritilishi shart!"}, status=400)

        try:
            doctor = DoctorAInfo.objects.get(id=doctor_id)
            doctor.delete()
            return JsonResponse({"success": True, "message": "❌ Doctor A ma'lumotlari o‘chirildi!"})
        except DoctorAInfo.DoesNotExist:
            return JsonResponse({"success": False, "error": "❌ Ma'lumot topilmadi!"}, status=404)
