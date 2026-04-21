from io import BytesIO

from django.contrib import admin
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from apps.medical.admin import SiteSettingsAdmin
from apps.medical.models import MainPageBanner, SiteSettings
from apps.members.models import CustomUser


class MainSettingsViewTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="settings_admin",
            password="testpass123",
            is_staff=True,
        )

    def make_image(self, name="banner.png", size=(400, 300), color=(12, 84, 255)):
        buffer = BytesIO()
        image = Image.new("RGB", size, color)
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return SimpleUploadedFile(name, buffer.read(), content_type="image/png")

    def test_settings_post_formats_phone_saves_rich_text_and_keeps_banner_dimensions(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("admin-setting-index"),
            {
                "site_name": "Doctor A",
                "contact_email": "info@example.com",
                "contact_phone": "901234567",
                "address": "<p>Toshkent shahri</p>",
                "working_hours": "<p>Dushanba - Juma 09:00 - 18:00</p>",
                "facebook_url": "",
                "telegram_url": "",
                "instagram_url": "",
                "youtube_url": "",
                "description_uz": "<p><strong>Banner tavsifi</strong></p>",
                "description_ru": "",
                "description_en": "",
                "description_de": "",
                "description_tr": "",
                "banner_image": self.make_image(),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("admin-setting-index"))

        site_settings = SiteSettings.objects.get()
        banner = MainPageBanner.objects.get()

        self.assertEqual(site_settings.contact_phone, "+998 90 123 45 67")
        self.assertEqual(site_settings.address, "<p>Toshkent shahri</p>")
        self.assertEqual(site_settings.working_hours, "<p>Dushanba - Juma 09:00 - 18:00</p>")
        self.assertEqual(banner.description["uz"], "<p><strong>Banner tavsifi</strong></p>")
        self.assertEqual(banner.image.width, 400)
        self.assertEqual(banner.image.height, 300)


class SiteSettingsAdminTests(TestCase):
    def test_sitesettings_admin_uses_existing_social_fields(self):
        admin_instance = SiteSettingsAdmin(SiteSettings, admin.site)

        field_names = []
        for _, options in admin_instance.fieldsets:
            for field in options.get("fields", ()):
                if isinstance(field, (list, tuple)):
                    field_names.extend(field)
                else:
                    field_names.append(field)

        self.assertIn("facebook_url", field_names)
        self.assertIn("telegram_url", field_names)
        self.assertIn("instagram_url", field_names)
        self.assertIn("youtube_url", field_names)
        self.assertNotIn("twitter_url", field_names)
        self.assertNotIn("linkedin_url", field_names)
