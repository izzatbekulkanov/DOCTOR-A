from django.db import models
from django.db import models
from django.utils.translation import gettext_lazy as _
# Create your models here.
from django.contrib.auth.models import User
from members.models import CustomUser


# Create your models here.
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

class Comment(models.Model):
    news = models.ForeignKey(
        News,
        on_delete=models.CASCADE,
        related_name="comments",
        help_text=_("Izoh berilgan yangilik")
    )
    full_name = models.CharField(
        max_length=255,
        help_text=_("Foydalanuvchining to'liq ismi")
    )
    phone_number = models.CharField(
        max_length=20,
        help_text=_("Foydalanuvchining telefon raqami")
    )
    text = models.TextField(
        help_text=_("Izoh matni")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Izoh qoldirilgan sana")
    )

    class Meta:
        verbose_name = _("Izoh")
        verbose_name_plural = _("Izohlar")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} - {self.news.title.get('uz', 'Noma’lum yangilik')}"

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
