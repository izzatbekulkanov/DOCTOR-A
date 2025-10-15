from django.db import models
from django.utils.translation import gettext_lazy as _
# Create your models here.
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from members.models import CustomUser


class SiteSettings(models.Model):
    # Sayt nomi
    site_name = models.CharField(max_length=255, help_text="Sayt nomini kiriting")

    # Sayt logotiplari
    logo_dark = models.ImageField(upload_to='logos/', null=True, blank=True, help_text="Dark rejim uchun logotip")
    logo_light = models.ImageField(upload_to='logos/', null=True, blank=True, help_text="Light rejim uchun logotip")

    # Videolar
    video1 = models.FileField(upload_to='videos/', null=True, blank=True, help_text="1-video faylni yuklang")
    video2 = models.FileField(upload_to='videos/', null=True, blank=True, help_text="2-video faylni yuklang")

    # Qo'shimcha sozlamalar
    contact_email = models.EmailField(null=True, blank=True, help_text="Aloqa uchun email manzil")
    contact_phone = models.CharField(max_length=20, null=True, blank=True, help_text="Aloqa uchun telefon raqami")
    address = models.TextField(null=True, blank=True, help_text="Kompaniya manzili")
    maintenance_mode = models.BooleanField(
        default=False,
        help_text="Saytni texnik xizmat ko'rsatish rejimiga o'tkazish"
    )

    # Ish vaqti
    working_hours = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Ish vaqti (masalan: Dushanba - Juma 9:00 - 17:00)"
    )

    # Ijtimoiy tarmoqlar uchun havolalar
    facebook_url = models.URLField(null=True, blank=True, help_text="Facebook sahifa URL")
    youtube_url = models.URLField(null=True, blank=True, help_text="YouTube sahifa URL")
    instagram_url = models.URLField(null=True, blank=True, help_text="Instagram sahifa URL")
    telegram_url = models.URLField(null=True, blank=True, help_text="Telegram sahifa URL")

    # Foydalanuvchi tomonidan yaratilgan va yangilangan vaqt
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sayt Sozlamalari"
        verbose_name_plural = "Sayt Sozlamalari"

    def __str__(self):
        return self.site_name


# Sayt Asosiy Rasmlari
class MainPageBanner(models.Model):
    image = models.ImageField(upload_to='banners/', help_text=_("1920x180 o'lchamdagi asosiy sahifa banner rasmi"))
    description = models.JSONField(default=dict, help_text=_("Har xil tillarda rasm tavsifi (JSON formatda)"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Asosiy sahifa banneri")
        verbose_name_plural = _("Asosiy sahifa bannerlari")

    def __str__(self):
        return f"Banner: {self.description.get('uz', 'Tavsif mavjud emas')[:30]}"

# Doctor A haqida ma'lumot
class DoctorAInfo(models.Model):
    title = models.JSONField(default=dict, help_text=_("Har xil tillarda sarlavha (JSON formatda)"))
    description = models.JSONField(default=dict, help_text=_("Har xil tillarda batafsil tavsif (JSON formatda)"))
    image = models.ImageField(upload_to='doctor_a/', help_text=_("Doctor A haqida ma'lumot rasmi"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Doctor A haqida ma'lumot")
        verbose_name_plural = _("Doctor A haqida ma'lumotlar")

    def __str__(self):
        return self.title.get('uz', 'Sarlavha mavjud emas')

# Aloqa Telefonlari
class ContactPhone(models.Model):
    phone_number = models.CharField(max_length=20, help_text=_("Telefon raqami (+998...) formatda kiriting"))

    # JSONField yordamida har xil tillarda tavsifni saqlash
    description = models.JSONField(default=dict, help_text=_(
        "Har xil tillarda telefon raqami haqida qisqacha tavsif (JSON formatda)"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Aloqa Telefoni")
        verbose_name_plural = _("Aloqa Telefonlari")

    def __str__(self):
        return self.phone_number

    def get_description(self, language_code='uz'):
        """ Til kodi asosida tavsifni olish """
        return self.description.get(language_code, self.description.get('uz', 'Tavsif yo‘q'))


class Partner(models.Model):
    # Ko'p tilli nom
    name = models.JSONField(default=dict, help_text=_("Har xil tillarda hamkor nomi (JSON formatda)"))
    # Ko'p tilli tavsif
    description = models.JSONField(default=dict, help_text=_("Har xil tillarda hamkor tavsifi (JSON formatda)"))
    # Hamkorning logotipi yoki rasmi
    logo = models.ImageField(upload_to='partners/', null=True, blank=True, help_text=_("Hamkorning logotipi"))
    # Hamkor veb-sayti havolasi
    website_url = models.URLField(null=True, blank=True, help_text=_("Hamkorning veb-sayti manzili"))
    # Chop etilgan sana
    created_at = models.DateTimeField(auto_now_add=True, help_text=_("Chop etilgan sana"))
    # Tahrirlangan sana
    updated_at = models.DateTimeField(auto_now=True, help_text=_("Oxirgi tahrir qilingan sana"))
    # Hamkor faolmi
    is_active = models.BooleanField(default=True, help_text=_("Hamkor faolmi?"))

    class Meta:
        verbose_name = _("Hamkor")
        verbose_name_plural = _("Hamkorlar")
        ordering = ['-created_at']

    def __str__(self):
        return self.name.get('uz', _('Nomi mavjud emas'))

    def get_description(self, lang_code='uz'):
        """
        Tavsifni til kodi asosida olish.
        """
        return self.description.get(lang_code, self.description.get('uz', _('Tavsif mavjud emas')))

class MedicalCheckupApplication(models.Model):
    full_name = models.CharField(max_length=255, verbose_name="Ism va familiya")
    phone_number = models.CharField(max_length=15, verbose_name="Telefon raqami")
    message = models.TextField(verbose_name="Xabar", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    is_seen = models.BooleanField(default=False, verbose_name="Ko‘rildi")  # Yangi maydon

    def __str__(self):
        return f"{self.full_name} - {self.phone_number}"

    class Meta:
        verbose_name = "Tibbiy ko'rik arizasi"
        verbose_name_plural = "Tibbiy ko'rik arizalari"
        ordering = ['-created_at']  # Yangidan eskisiga tartiblash

# Klinikadagi qurilmalar ro'yxati
class ClinicEquipment(models.Model):
    name = models.JSONField(default=dict, help_text=_("Har xil tillarda qurilma nomi (JSON formatda)"))
    description = models.JSONField(default=dict, help_text=_("Har xil tillarda qurilma haqida batafsil ma'lumot (JSON formatda)"))
    image = models.ImageField(upload_to='equipment/', help_text=_("Qurilma rasmi (masalan, 800x600 o'lchamda)"))
    is_active = models.BooleanField(default=True, help_text=_("Qurilma faol yoki faol emasligini belgilaydi"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Klinika qurilmasi")
        verbose_name_plural = _("Klinika qurilmalari")

    def __str__(self):
        return self.name.get('uz', 'Nomi mavjud emas')

    def get_name(self, language_code='uz'):
        """ Til kodi asosida qurilma nomini olish """
        return self.name.get(language_code, self.name.get('uz', 'Nomi mavjud emas'))

    def get_description(self, language_code='uz'):
        """ Til kodi asosida qurilma tavsifini olish """
        return self.description.get(language_code, self.description.get('uz', 'Tavsif yo‘q'))

import re

class Video(models.Model):
    YOUTUBE_REGEX = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:embed\/|watch\?v=)|youtu\.be\/)([A-Za-z0-9_-]+)'

    youtube_embed_validator = RegexValidator(
        regex=YOUTUBE_REGEX,
        message=_("To‘g‘ri YouTube URL yoki Video ID kiriting (masalan, https://www.youtube.com/embed/07NL6SlDRUY yoki 07NL6SlDRUY).")
    )

    title = models.JSONField(default=dict, help_text=_("Har xil tillarda video sarlavhasi (JSON formatda)"))
    embed_url = models.CharField(
        max_length=50,
        validators=[youtube_embed_validator],
        help_text=_("YouTube video ID (masalan, 07NL6SlDRUY)")
    )
    is_active = models.BooleanField(default=True, help_text=_("Video faol yoki faol emasligini belgilaydi"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Video")
        verbose_name_plural = _("Videolar")

    def __str__(self):
        return self.title.get('uz', 'Sarlavha mavjud emas')

    def get_title(self, language_code='uz'):
        return self.title.get(language_code, self.title.get('uz', 'Sarlavha mavjud emas'))

    def clean_embed_url(self):
        """Video URL’dan faqat video ID’ni ajratib olish."""
        match = re.search(self.YOUTUBE_REGEX, self.embed_url)
        if match:
            self.embed_url = match.group(1)

    def save(self, *args, **kwargs):
        self.clean_embed_url()
        super().save(*args, **kwargs)

    def get_embed_url(self):
        """To‘liq iframe URL hosil qilish."""
        return f"https://www.youtube.com/embed/{self.embed_url}"