from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.utils.translation import gettext_lazy as _
from ..models import MainPageBanner, DoctorAInfo, SiteSettings, ContactPhone
from ..forms import MainPageBannerForm, DoctorAInfoForm

# Tillar ro'yxati
LANGUAGES = [
    ('uz', _('Uzbek')),
    ('kk', _('Kazakh')),
    ('tr', _('Turkish')),
    ('ru', _('Russian')),
    ('en', _('English')),
    ('de', _('German')),
    ('fr', _('French')),
    ('ko', _('Korean')),
]

class SettingView(View):
    template_name = 'administrator/views/settings.html'

    def get(self, request):
        settings = SiteSettings.objects.first()
        contact_phones = ContactPhone.objects.all()
        banners = MainPageBanner.objects.all()
        doctor_a_info = DoctorAInfo.objects.all()

        return render(request, self.template_name, {
            'settings': settings,
            'contact_phones': contact_phones,
            'banners': banners,
            'doctor_a_info': doctor_a_info,
            'languages': LANGUAGES,
        })

    def post(self, request):
        # Manage site settings
        if 'site_name' in request.POST:
            settings = SiteSettings.objects.first()
            if settings:
                settings.site_name = request.POST.get('site_name')
                settings.contact_email = request.POST.get('contact_email')
                settings.contact_phone = request.POST.get('contact_phone')
                settings.address = request.POST.get('address')
                settings.maintenance_mode = 'maintenance_mode' in request.POST

                if 'logo_dark' in request.FILES:
                    settings.logo_dark = request.FILES['logo_dark']
                if 'logo_light' in request.FILES:
                    settings.logo_light = request.FILES['logo_light']

                settings.save()
            else:
                SiteSettings.objects.create(
                    site_name=request.POST.get('site_name'),
                    contact_email=request.POST.get('contact_email'),
                    contact_phone=request.POST.get('contact_phone'),
                    address=request.POST.get('address'),
                    maintenance_mode='maintenance_mode' in request.POST,
                    logo_dark=request.FILES.get('logo_dark'),
                    logo_light=request.FILES.get('logo_light'),
                )
            return JsonResponse({'status': 'success', 'message': 'Sayt sozlamalari saqlandi!'})

        # Manage contact phones
        elif 'phone_number' in request.POST:
            phone_number = request.POST.get('phone_number')
            description = {}

            for code, _ in LANGUAGES:
                description[code] = request.POST.get(f'description_{code}', '')

            if not description.get('uz'):
                description['uz'] = "Tavsif mavjud emas"

            if not phone_number:
                return JsonResponse({'status': 'error', 'message': 'Telefon raqami bo\'sh bo\'lishi mumkin emas!'})
            if ContactPhone.objects.filter(phone_number=phone_number).exists():
                return JsonResponse({'status': 'error', 'message': 'Bu telefon raqami allaqachon mavjud!'})

            ContactPhone.objects.create(phone_number=phone_number, description=description)
            return JsonResponse({'status': 'success', 'message': 'Telefon muvaffaqiyatli qo\'shildi!'})

        # Manage banners
        elif 'banner_image' in request.POST:
            print("DEBUG: Banner submission started")  # Debug start of banner handling
            image = request.FILES.get('banner_image')
            description = {}
            print(f"DEBUG: Received image: {image}")  # Log the received image

            for code, _ in LANGUAGES:
                description[code] = request.POST.get(f'banner_description_{code}', '')
                print(f"DEBUG: Description for {code}: {description[code]}")  # Log description for each language

            if not description.get('uz'):
                description['uz'] = "Tavsif mavjud emas"
                print("DEBUG: Default Uzbek description added")  # Log default Uzbek description

            # Create the banner
            MainPageBanner.objects.create(image=image, description=description)
            print(f"DEBUG: Banner created with image {image} and description {description}")  # Log successful creation
            return JsonResponse({'status': 'success', 'message': 'Banner muvaffaqiyatli qo\'shildi!'})

        # Manage Doctor A Info
        elif 'doctor_title' in request.POST:
            print("DEBUG: Doctor A Info submission started")  # Debug start of Doctor A handling
            title = {}
            description = {}
            image = request.FILES.get('doctor_image')
            print(f"DEBUG: Received image: {image}")  # Log the received image

            for code, _ in LANGUAGES:
                title[code] = request.POST.get(f'doctor_title_{code}', '')
                description[code] = request.POST.get(f'doctor_description_{code}', '')
                print(f"DEBUG: Title for {code}: {title[code]}")  # Log title for each language
                print(f"DEBUG: Description for {code}: {description[code]}")  # Log description for each language

            if not title.get('uz'):
                title['uz'] = "Sarlavha mavjud emas"
                print("DEBUG: Default Uzbek title added")  # Log default Uzbek title
            if not description.get('uz'):
                description['uz'] = "Tavsif mavjud emas"
                print("DEBUG: Default Uzbek description added")  # Log default Uzbek description

            # Create the Doctor A Info
            DoctorAInfo.objects.create(title=title, description=description, image=image)
            print(
                f"DEBUG: Doctor A Info created with title {title}, description {description}, and image {image}")  # Log successful creation
            return JsonResponse(
                {'status': 'success', 'message': 'Doctor A haqida ma\'lumot muvaffaqiyatli qo\'shildi!'})

        return JsonResponse({'status': 'error', 'message': 'Noto\'g\'ri so\'rov!'})

# Function to delete banners
def banner_delete(request, banner_id):
    banner = get_object_or_404(MainPageBanner, id=banner_id)
    banner.delete()
    return redirect('setting-view')

# Function to delete Doctor A Info
def doctor_info_delete(request, info_id):
    info = get_object_or_404(DoctorAInfo, id=info_id)
    info.delete()
    return redirect('setting-view')

def contact_phone_delete(request, phone_id):
    phone = get_object_or_404(ContactPhone, id=phone_id)
    phone.delete()
    return redirect('setting-view')

# MainPageBanner Yaratish va Tahrirlash
def manage_main_page_banner(request, banner_id=None):
    if banner_id:
        banner = get_object_or_404(MainPageBanner, id=banner_id)
    else:
        banner = None

    if request.method == 'POST':
        form = MainPageBannerForm(request.POST, request.FILES, instance=banner)
        if form.is_valid():
            form.save()
            return redirect('banner-list')  # O'zingizning URL nomingizni yozing
    else:
        form = MainPageBannerForm(instance=banner)

    return render(request, 'manage_main_page_banner.html', {'form': form})


# DoctorAInfo Yaratish va Tahrirlash
def manage_doctor_a_info(request, info_id=None):
    if info_id:
        info = get_object_or_404(DoctorAInfo, id=info_id)
    else:
        info = None

    if request.method == 'POST':
        form = DoctorAInfoForm(request.POST, request.FILES, instance=info)
        if form.is_valid():
            form.save()
            return redirect('doctor-a-info-list')  # O'zingizning URL nomingizni yozing
    else:
        form = DoctorAInfoForm(instance=info)

    return render(request, 'manage_doctor_a_info.html', {'form': form})