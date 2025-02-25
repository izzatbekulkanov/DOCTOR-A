from django.db import models
from django.utils.translation import gettext_lazy as _
# Create your models here.
from django.contrib.auth.models import User

from members.models import CustomUser


class SiteSettings(models.Model):
    # Sayt nomi
    site_name = models.CharField(max_length=255, help_text="Sayt nomini kiriting")

    # Sayt logotiplari
    logo_dark = models.ImageField(upload_to='logos/', null=True, blank=True, help_text="Dark rejim uchun logotip")
    logo_light = models.ImageField(upload_to='logos/', null=True, blank=True, help_text="Light rejim uchun logotip")

    # Qo'shimcha sozlamalar
    contact_email = models.EmailField(null=True, blank=True, help_text="Aloqa uchun email manzil")
    contact_phone = models.CharField(max_length=20, null=True, blank=True, help_text="Aloqa uchun telefon raqami")
    address = models.TextField(null=True, blank=True, help_text="Kompaniya manzili")
    maintenance_mode = models.BooleanField(default=False,
                                           help_text="Saytni texnik xizmat ko'rsatish rejimiga o'tkazish")

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


class News(models.Model):
    # Ko'p tilli sarlavha
    title = models.JSONField(default=dict, help_text=_("Har xil tillarda yangiliklar sarlavhasi (JSON formatda)"))
    # Ko'p tilli mazmun
    content = models.JSONField(default=dict, help_text=_("Har xil tillarda yangilik mazmuni (JSON formatda)"))
    # Rasm
    image = models.ImageField(upload_to='news_images/', null=True, blank=True, help_text=_("Yangiliklar rasmi"))
    # Chop etilgan sana
    published_date = models.DateTimeField(auto_now_add=True, help_text=_("Chop etilgan sana"))
    created_at = models.DateTimeField(auto_now_add=True, help_text=_("Yaratilgan sana"))
    # Tahrirlangan sana
    updated_at = models.DateTimeField(auto_now=True, help_text=_("Oxirgi tahrir qilingan sana"))
    # Chop etilgan holati
    is_published = models.BooleanField(default=False, help_text=_("Chop etilganmi?"))
    # Muallif
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="news_posts",
        help_text=_("Yangilik muallifi")
    )
    # Ko'rishlar soni
    views_count = models.PositiveIntegerField(default=0, help_text=_("Yangilik qancha marta ko'rilgan"))

    class Meta:
        verbose_name = _("Yangilik")
        verbose_name_plural = _("Yangiliklar")
        ordering = ['-published_date']

    def __str__(self):
        return self.title.get('uz', _('Sarlavha mavjud emas'))

    def get_content(self, lang_code='uz'):
        """
        Mazmunni til kodi asosida olish.
        """
        return self.content.get(lang_code, self.content.get('uz', _('Mazmun mavjud emas')))

    def increment_views(self):
        """
        Ko'rishlar sonini 1 taga oshirish uchun yordamchi funksiya.
        """
        self.views_count += 1
        self.save(update_fields=['views_count'])


class Announcement(models.Model):
    # Ko'p tilli sarlavha
    title = models.JSONField(default=dict, help_text=_("Har xil tillarda e'lon sarlavhasi (JSON formatda)"))
    # Ko'p tilli mazmun
    content = models.JSONField(default=dict, help_text=_("Har xil tillarda e'lon mazmuni (JSON formatda)"))
    # Chop etilgan sana
    published_date = models.DateTimeField(auto_now_add=True, help_text=_("Chop etilgan sana"))
    # Tahrirlangan sana
    updated_at = models.DateTimeField(auto_now=True, help_text=_("Oxirgi tahrir qilingan sana"))
    # Chop etilgan holati
    is_published = models.BooleanField(default=False, help_text=_("Chop etilganmi?"))
    # Muallif
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="announcements",
        help_text=_("E'lon muallifi")
    )
    # Ko'rishlar soni
    views_count = models.PositiveIntegerField(default=0, help_text=_("E'lon qancha marta ko'rilgan"))

    class Meta:
        verbose_name = _("E'lon")
        verbose_name_plural = _("E'lonlar")
        ordering = ['-published_date']

    def __str__(self):
        return self.title.get('uz', _('Sarlavha mavjud emas'))

    def get_content(self, lang_code='uz'):
        """
        Mazmunni til kodi asosida olish.
        """
        return self.content.get(lang_code, self.content.get('uz', _('Mazmun mavjud emas')))

    def increment_views(self):
        """
        Ko'rishlar sonini 1 taga oshirish uchun yordamchi funksiya.
        """
        self.views_count += 1
        self.save(update_fields=['views_count'])


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
