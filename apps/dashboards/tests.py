from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from apps.medical.models import MainPageBanner, SiteSettings, MedicalCheckupApplication
from members.models import Appointment, CustomUser, EmployeeActivityHistory


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
            description="Ginekologiya kursi",
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
        self.assertNotContains(response, "FRONTEND DEBUG")


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
