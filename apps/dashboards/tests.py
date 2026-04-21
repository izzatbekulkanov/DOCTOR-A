from io import BytesIO
from html import unescape

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from apps.medical.models import ClinicEquipment, ClinicService, MainPageBanner, SiteSettings, MedicalCheckupApplication
from apps.news.models import Announcement
from apps.members.models import Appointment, CustomUser, EmployeeActivityHistory


class AboutStyleTwoViewTests(TestCase):
    def make_image(self, name="about-banner.png", size=(640, 320), color=(220, 30, 30)):
        buffer = BytesIO()
        image = Image.new("RGB", size, color)
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return SimpleUploadedFile(name, buffer.read(), content_type="image/png")

    def test_about_page_renders_banner_description_as_rich_text(self):
        MainPageBanner.objects.create(
            image=self.make_image(),
            description={"uz": "<p><strong>Banner</strong> tavsifi</p>"},
        )

        response = self.client.get(reverse("landing-v1-about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<strong>Banner</strong>", html=True)
        self.assertNotContains(response, "&lt;strong&gt;Banner&lt;/strong&gt;")

    def test_about_page_footer_uses_site_settings_address_and_working_hours(self):
        SiteSettings.objects.create(
            site_name="Doctor A",
            address="<p>Test manzil</p>",
            working_hours="<p>09:00 - 18:00</p>",
        )

        response = self.client.get(reverse("landing-v1-about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<p>Test manzil</p>", html=True)
        self.assertContains(response, "<p>09:00 - 18:00</p>", html=True)

    def test_about_page_footer_localizes_footer_contact_and_hours_blocks(self):
        SiteSettings.objects.create(
            site_name="Doctor A",
            contact_phone="+998 69 226 00 00",
            contact_email="doctoramedclink2025@gamil.com",
        )
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"

        response = self.client.get(reverse("landing-v1-about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Working Hours")
        self.assertContains(response, "Contact")
        self.assertContains(response, "Address and Landmark")
        self.assertContains(response, "Monday - Saturday: 08:00 - 16:00")
        self.assertContains(response, "Address: 2 Boburshoh Street, Namangan city.")
        self.assertContains(response, "+998 69 226 00 00")
        self.assertContains(response, "doctoramedclink2025@gamil.com")


class DoctorLandingDetailViewTests(TestCase):
    def test_doctor_detail_renders_full_profile_and_strips_debug_bio_wrapper(self):
        doctor = CustomUser.objects.create(
            username="doctor11",
            full_name="Shifokor Test",
            phone_number="+998907591028",
            email="doctor@example.com",
            is_active_employee=True,
            is_superuser=False,
            job_title="GINEKOLOG",
            medical_specialty="Terapevt",
            professional_license_number="DIP-7788",
            shift_schedule="Du-Sha 09:00-18:00",
            telegram_username="@doctor_test",
            instagram_username="doctor_test",
            address="<p>Namangan shahri</p>",
            employee_id="EMP-11",
            bio="----------------------------------------- FRONTEND DEBUG: Yuborilayotgan bio qiymati: <p>Yangi tajriba</p> -----------------------------------------",
        )
        EmployeeActivityHistory.objects.create(
            user=doctor,
            activity_name="Malaka oshirish",
            activity_type="training",
            description="<p><strong>Ginekologiya</strong> kursi</p>",
            is_completed=True,
        )

        response = self.client.get(reverse("landing-v1-doctor-detail", args=[doctor.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GINEKOLOG")
        self.assertContains(response, "+998907591028")
        self.assertContains(response, "Terapevt")
        self.assertContains(response, "DIP-7788")
        self.assertContains(response, "Malaka oshirish")
        self.assertContains(response, "Yangi tajriba")
        self.assertContains(response, "<strong>Ginekologiya</strong>", html=True)
        self.assertNotContains(response, "&lt;strong&gt;Ginekologiya&lt;/strong&gt;")
        self.assertNotContains(response, "FRONTEND DEBUG")


class DoctorGridViewTests(TestCase):
    def test_doctor_grid_shows_only_supported_social_links(self):
        CustomUser.objects.create(
            username="doctor_grid",
            full_name="Grid Doctor",
            is_active_employee=True,
            is_superuser=False,
            medical_specialty="Nevrolog",
            telegram_username="@grid_doctor",
            instagram_username="grid_doctor",
        )

        response = self.client.get(reverse("landing-v1-doctors"))
        content = response.content.decode("utf-8")
        doctor_card_markup = content.split('<div class="single-doctor">', 1)[1].split("</ul>", 1)[0]

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "https://t.me/grid_doctor")
        self.assertContains(response, "https://instagram.com/grid_doctor")
        self.assertIn("bxl-telegram", doctor_card_markup)
        self.assertIn("bxl-instagram", doctor_card_markup)
        self.assertNotIn("bxl-facebook", doctor_card_markup)
        self.assertNotIn("bxl-twitter", doctor_card_markup)
        self.assertNotIn("bxl-linkedin", doctor_card_markup)


class ContactStyleTwoViewTests(TestCase):
    def setUp(self):
        self.employee = CustomUser.objects.create(
            username="doctor_contact",
            full_name="Qabul Doctor",
            is_active_employee=True,
            is_superuser=False,
            job_title="Kardiolog",
        )

    def test_contact_page_renders_active_employees_for_appointment_form(self):
        response = self.client.get(reverse("landing-v1-contact"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Qabul Doctor")
        self.assertContains(response, "Qabulga yozilish")

    def test_contact_page_renders_site_settings_address_as_rich_text(self):
        SiteSettings.objects.create(
            site_name="Doctor A",
            address="<p><strong>Test manzil</strong></p>",
        )

        response = self.client.get(reverse("landing-v1-contact"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<strong>Test manzil</strong>", html=True)
        self.assertNotContains(response, "&lt;strong&gt;Test manzil&lt;/strong&gt;")

    def test_contact_page_creates_appointment_request(self):
        response = self.client.post(
            reverse("landing-v1-contact"),
            {
                "form_type": "appointment",
                "appointment_name": "Bemor Test",
                "appointment_phone": "+998 90 111 22 33",
                "appointment_message": "Konsultatsiya kerak",
                "employee_id": self.employee.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "success", "form": "appointment"})

        appointment = Appointment.objects.get()
        self.assertEqual(appointment.full_name, "Bemor Test")
        self.assertEqual(appointment.phone_number, "+998901112233")
        self.assertEqual(appointment.message, "Konsultatsiya kerak")
        self.assertEqual(appointment.employee, self.employee)

    def test_contact_page_creates_medical_checkup_request(self):
        response = self.client.post(
            reverse("landing-v1-contact"),
            {
                "form_type": "contact",
                "name": "Oddiy Murojaat",
                "phone": "+998 90 222 33 44",
                "message": "Qayta aloqa kerak",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "success", "form": "contact"})

        application = MedicalCheckupApplication.objects.get()
        self.assertEqual(application.full_name, "Oddiy Murojaat")
        self.assertEqual(application.phone_number, "+998902223344")
        self.assertEqual(application.message, "Qayta aloqa kerak")


class LandingPageV1ViewTests(TestCase):
    def make_image(self, name="doctor-card.png", size=(640, 640), color=(210, 40, 40)):
        buffer = BytesIO()
        image = Image.new("RGB", size, color)
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return SimpleUploadedFile(name, buffer.read(), content_type="image/png")

    def test_landing_hero_buttons_and_footer_service_links_render(self):
        first_service = ClinicService.objects.create(
            title={"uz": "Kardiologiya", "en": "Cardiology"},
            summary={"uz": "Yurak xizmati"},
            icon_class="flaticon-heart",
            sort_order=1,
            is_active=True,
        )
        ClinicService.objects.create(
            title={"uz": "Nevrologiya", "en": "Neurology"},
            summary={"uz": "Asab tizimi xizmati"},
            icon_class="flaticon-brain",
            sort_order=2,
            is_active=True,
        )

        response = self.client.get(reverse("landing-v1"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("landing-v1-services"))
        self.assertContains(response, reverse("landing-v1-contact"))
        self.assertContains(response, "Kardiologiya")
        self.assertContains(response, f'{reverse("landing-v1-services")}#service-{first_service.id}')

    def test_landing_doctors_section_uses_available_contact_links_and_view_all_button(self):
        doctor = CustomUser.objects.create(
            username="doctor-home",
            full_name="Shifokor Bosh Sahifa",
            is_active_employee=True,
            is_superuser=False,
            medical_specialty="Nevrolog",
            telegram_username="@doctor_home",
            instagram_username="@doctor_home_insta",
            phone_number="+998901112233",
            profile_picture=self.make_image(),
        )

        response = self.client.get(reverse("landing-v1"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("landing-v1-doctors"))
        self.assertContains(response, "section-title-action")
        self.assertContains(response, "Barchasini ko&#x27;rish")
        self.assertContains(response, f"https://t.me/{doctor.telegram_username.lstrip('@')}")
        self.assertContains(response, f"https://instagram.com/{doctor.instagram_username.lstrip('@')}")
        self.assertContains(response, f"tel:{doctor.phone_number}")
        self.assertContains(response, reverse("landing-v1-doctor-detail", args=[doctor.id]))
        doctor_card = response.content.decode("utf-8").split("Shifokor Bosh Sahifa", 1)[1].split("</ul>", 1)[0]
        self.assertNotIn("bxl-facebook", doctor_card)
        self.assertNotIn("bx-envelope", doctor_card)
        self.assertIn("doctor-contact-hint", doctor_card)
        self.assertIn(doctor.phone_number, doctor_card)
        self.assertIn("bx-right-arrow-alt", doctor_card)

    def test_landing_static_sections_follow_active_language(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        response_en = self.client.get(reverse("landing-v1"))

        self.assertEqual(response_en.status_code, 200)
        self.assertContains(response_en, "Comprehensive medical care for every stage of treatment")
        self.assertContains(response_en, "Our Trusted Partners")

        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "uz"
        response_uz = self.client.get(reverse("landing-v1"))

        self.assertEqual(response_uz.status_code, 200)
        self.assertContains(response_uz, "Har bir davolash bosqichi uchun zamonaviy va ishonchli tibbiy xizmatlar")
        self.assertContains(response_uz, "Bizning ishonchli hamkorlarimiz")


class AnnouncementLandingDetailViewTests(TestCase):
    def test_announcement_detail_renders_rich_text_content(self):
        announcement = Announcement.objects.create(
            title={"uz": "Muhim e'lon"},
            content={"uz": "<p><strong>Rich</strong> mazmun</p>"},
            is_published=True,
        )

        response = self.client.get(reverse("landing-v1-announcement-detail", args=[announcement.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<strong>Rich</strong>", html=True)
        self.assertNotContains(response, "&lt;strong&gt;Rich&lt;/strong&gt;")


class EquipmentLandingDetailViewTests(TestCase):
    def make_image(self, name="equipment.png", size=(640, 320), color=(40, 120, 220)):
        buffer = BytesIO()
        image = Image.new("RGB", size, color)
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return SimpleUploadedFile(name, buffer.read(), content_type="image/png")

    def test_equipment_detail_renders_rich_text_description(self):
        equipment = ClinicEquipment.objects.create(
            name={"uz": "MRI"},
            description={"uz": "<p><strong>Yuqori</strong> aniqlik</p>"},
            image=self.make_image(),
            is_active=True,
        )

        response = self.client.get(reverse("landing-v1-equipment-detail", args=[equipment.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<strong>Yuqori</strong>", html=True)
        self.assertNotContains(response, "&lt;strong&gt;Yuqori&lt;/strong&gt;")

    def test_equipment_detail_shows_derived_category_label(self):
        equipment = ClinicEquipment.objects.create(
            name={"uz": "MRT"},
            description={"uz": "<p>Tomografiya tizimi</p>"},
            image=self.make_image("mrt.png"),
            is_active=True,
        )

        response = self.client.get(reverse("landing-v1-equipment-detail", args=[equipment.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tasvirlash")
        self.assertNotContains(response, "General")

    def test_equipment_list_builds_dynamic_capabilities_and_categories(self):
        ClinicEquipment.objects.create(
            name={"uz": "MRT"},
            description={"uz": "<p>Tomografiya tizimi</p>"},
            image=self.make_image("mrt-list.png"),
            is_active=True,
        )
        ClinicEquipment.objects.create(
            name={"uz": "UZI"},
            description={"uz": "<p>Ultrasound diagnostika</p>"},
            image=self.make_image("uzi-list.png"),
            is_active=True,
        )
        ClinicEquipment.objects.create(
            name={"uz": "Ventilator"},
            description={"uz": "<p>Critical care support</p>"},
            image=self.make_image("ventilator-list.png"),
            is_active=True,
        )

        response = self.client.get(reverse("landing-v1-equipment"))
        content = unescape(response.content.decode("utf-8"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("Tomografiya va yuqori aniqlikdagi tasvirlash (1 ta uskuna)", content)
        self.assertIn("Skrining va funktsional diagnostika (1 ta uskuna)", content)
        self.assertIn("Reanimatsiya va hayotni qo'llab-quvvatlash (1 ta uskuna)", content)
        self.assertIn("Tasvirlash", content)
        self.assertIn("Diagnostika", content)
        self.assertIn("Reanimatsiya", content)
        self.assertNotIn("Favqulodda yurak javobi", content)
