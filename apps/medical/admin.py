from django.contrib import admin
from django.utils.html import format_html
from django_json_widget.widgets import JSONEditorWidget
from django.db import models
from django.utils.translation import gettext_lazy as _


from .models import (
    SiteSettings, MainPageBanner, DoctorAInfo, ContactPhone, Partner, MedicalCheckupApplication, ClinicEquipment, Video
)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """ Sayt Sozlamalarini Boshqarish """
    list_display = ('site_name', 'contact_email', 'contact_phone', 'maintenance_mode', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ("Asosiy Sozlamalar", {
            'fields': ('site_name', 'contact_email', 'contact_phone', 'address', 'maintenance_mode')
        }),
        ("Logotiplar", {
            'fields': ('logo_dark', 'logo_light')
        }),
        ("Ijtimoiy Tarmoqlar", {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url')
        }),
        ("Tizim ma'lumotlari", {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def has_add_permission(self, request):
        """ Faqat bitta SiteSettings yozuvi bo‘lishiga ruxsat berish """
        return not SiteSettings.objects.exists()


@admin.register(MainPageBanner)
class MainPageBannerAdmin(admin.ModelAdmin):
    """ Asosiy sahifa bannerlarini boshqarish """
    list_display = ('id', 'preview_image', 'created_at', 'updated_at')
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

    def preview_image(self, obj):
        """ Banner rasmini kichik ko‘rinishda ko‘rsatish """
        if obj.image:
            return format_html('<img src="{}" width="100" height="50" style="border-radius:5px;">', obj.image.url)
        return "Rasm yo‘q"

    preview_image.short_description = "Banner rasm"


@admin.register(DoctorAInfo)
class DoctorAInfoAdmin(admin.ModelAdmin):
    """ Doctor A haqida ma’lumotlarni boshqarish """
    list_display = ('id', 'preview_image', 'created_at', 'updated_at')
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

    def preview_image(self, obj):
        """ Doctor A rasmi kichik ko‘rinishda """
        if obj.image:
            return format_html('<img src="{}" width="100" height="50" style="border-radius:5px;">', obj.image.url)
        return "Rasm yo‘q"

    preview_image.short_description = "Doctor A rasmi"


@admin.register(ContactPhone)
class ContactPhoneAdmin(admin.ModelAdmin):
    """ Aloqa Telefonlarini boshqarish """
    list_display = ('phone_number', 'created_at')
    search_fields = ('phone_number',)
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }





@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    """ Hamkorlarni boshqarish """
    list_display = ('id', 'name_uz', 'preview_logo', 'website_url', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    list_editable = ('is_active',)
    ordering = ['-created_at']
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

    def name_uz(self, obj):
        """ O‘zbek tilidagi nomini chiqarish """
        return obj.name.get('uz', 'Noma’lum')

    name_uz.short_description = "Hamkor nomi (UZ)"

    def preview_logo(self, obj):
        """ Hamkor logotipini kichik ko‘rinishda chiqarish """
        if obj.logo:
            return format_html('<img src="{}" width="100" height="50" style="border-radius:5px;">', obj.logo.url)
        return "Rasm yo‘q"

    preview_logo.short_description = "Logotip"




@admin.register(MedicalCheckupApplication)
class MedicalCheckupApplicationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone_number", "created_at")
    search_fields = ("full_name", "phone_number")
    list_filter = ("created_at",)



# ClinicEquipment uchun admin
@admin.register(ClinicEquipment)
class ClinicEquipmentAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'get_description_preview', 'image', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('name__uz', 'description__uz')
    list_editable = ('is_active',)  # Faollikni to‘g‘ridan-to‘g‘ri ro‘yxatda o‘zgartirish
    fieldsets = (
        (_("Qurilma ma'lumotlari"), {
            'fields': ('name', 'description', 'image', 'is_active'),
        }),
        (_("Vaqt ma'lumotlari"), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    def get_name(self, obj):
        return obj.name.get('uz', 'Nomi mavjud emas')
    get_name.short_description = _("Nomi (O‘zbek)")

    def get_description_preview(self, obj):
        return obj.description.get('uz', 'Tavsif yo‘q')[:30]
    get_description_preview.short_description = _("Tavsif (O‘zbek)")


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("get_title", "video_preview", "is_active", "created_at")
    list_filter = ("is_active", "created_at", "updated_at")
    search_fields = ("title__uz", "title__ru", "title__en")
    readonly_fields = ("created_at", "updated_at", "video_preview")

    def video_preview(self, obj):
        """Admin panelida YouTube videosining oldindan ko‘rinishi."""
        return format_html(
            '<iframe width="200" height="113" src="{}" frameborder="0" allowfullscreen></iframe>',
            obj.get_embed_url()
        ) if obj.embed_url else "Video yo‘q"
    video_preview.short_description = "Oldindan ko‘rish"