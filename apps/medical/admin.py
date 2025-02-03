from django.contrib import admin
from django.utils.html import format_html
from django_json_widget.widgets import JSONEditorWidget
from django.db import models

from .models import (
    SiteSettings, MainPageBanner, DoctorAInfo, ContactPhone,
    News, Announcement, Partner
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


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    """ Yangiliklarni boshqarish """
    list_display = ('id', 'title_uz', 'published_date', 'author', 'views_count', 'is_published')
    list_filter = ('is_published', 'published_date', 'author')
    search_fields = ('title',)
    date_hierarchy = 'published_date'
    ordering = ['-published_date']
    list_editable = ('is_published',)
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

    def title_uz(self, obj):
        """ O‘zbek tilidagi sarlavhani chiqarish """
        return obj.title.get('uz', 'Noma’lum')

    title_uz.short_description = "Sarlavha (UZ)"


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """ E’lonlarni boshqarish """
    list_display = ('id', 'title_uz', 'published_date', 'author', 'views_count', 'is_published')
    list_filter = ('is_published', 'published_date', 'author')
    search_fields = ('title',)
    date_hierarchy = 'published_date'
    ordering = ['-published_date']
    list_editable = ('is_published',)
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

    def title_uz(self, obj):
        """ O‘zbek tilidagi sarlavhani chiqarish """
        return obj.title.get('uz', 'Noma’lum')

    title_uz.short_description = "Sarlavha (UZ)"


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


