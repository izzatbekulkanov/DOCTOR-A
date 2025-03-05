from django.contrib import admin
from django_json_widget.widgets import JSONEditorWidget
from django.db import models
from apps.news.models import News, Announcement, Comment


# Register your models here.

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


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'phone_number', 'news_title', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('full_name', 'phone_number', 'text')

    def news_title(self, obj):
        return obj.news.title.get('uz', 'Noma’lum yangilik')

    news_title.short_description = "Yangilik"
