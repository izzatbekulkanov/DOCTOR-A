from django.contrib import admin

from medical.models import SiteSettings, MainPageBanner, DoctorAInfo, ContactPhone, Announcement, Partner, News


# Register your models here.
@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'contact_email', 'contact_phone', 'maintenance_mode', 'updated_at')
    list_editable = ('maintenance_mode',)
    search_fields = ('site_name', 'contact_email', 'contact_phone')
    fieldsets = (
        ('Sayt haqida ma\'lumotlar', {
            'fields': ('site_name', 'logo_dark', 'logo_light')
        }),
        ('Aloqa ma\'lumotlari', {
            'fields': ('contact_email', 'contact_phone', 'address')
        }),
        ('Ijtimoiy tarmoqlar', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url')
        }),
        ('Boshqaruv', {
            'fields': ('maintenance_mode',)
        }),
    )


@admin.register(MainPageBanner)
class MainPageBannerAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_description_uz', 'created_at', 'updated_at')
    search_fields = ('description__uz',)

    def get_description_uz(self, obj):
        return obj.description.get('uz', 'Tavsif mavjud emas')
    get_description_uz.short_description = "Tavsif (uz)"


@admin.register(DoctorAInfo)
class DoctorAInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_title_uz', 'created_at', 'updated_at')
    search_fields = ('title__uz',)

    def get_title_uz(self, obj):
        return obj.title.get('uz', 'Sarlavha mavjud emas')
    get_title_uz.short_description = "Sarlavha (uz)"


@admin.register(ContactPhone)
class ContactPhoneAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'description', 'created_at')
    search_fields = ('phone_number', 'description')
    list_filter = ('created_at', 'updated_at')


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_title', 'author', 'is_published', 'views_count', 'published_date']
    search_fields = ['title__uz', 'title__en']
    list_filter = ['is_published', 'published_date', 'author']
    ordering = ['-published_date']

    def get_title(self, obj):
        return obj.title.get('uz', 'Nomi yo‘q')
    get_title.short_description = 'Sarlavha (O‘zbekcha)'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_title', 'author', 'is_published', 'views_count', 'published_date']
    search_fields = ['title__uz', 'title__en']
    list_filter = ['is_published', 'published_date', 'author']
    ordering = ['-published_date']

    def get_title(self, obj):
        return obj.title.get('uz', 'Nomi yo‘q')
    get_title.short_description = 'Sarlavha (O‘zbekcha)'


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_name', 'is_active', 'website_url', 'created_at']
    search_fields = ['name__uz', 'name__en']
    list_filter = ['is_active', 'created_at']
    ordering = ['-created_at']

    def get_name(self, obj):
        return obj.name.get('uz', 'Nomi yo‘q')
    get_name.short_description = 'Hamkor Nomi (O‘zbekcha)'