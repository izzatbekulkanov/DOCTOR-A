from django.conf import settings
from rest_framework import serializers

from apps.medical.models import MedicalCheckupApplication
from apps.news.models import News, Announcement


class NewsSerializer(serializers.ModelSerializer):
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)

    class Meta:
        model = News
        fields = ['id', 'title', 'content', 'image', 'published_date', 'views_count', 'comments_count']


class AnnouncementSerializer(serializers.ModelSerializer):
    title_i18n = serializers.JSONField(source="title", read_only=True)
    content_i18n = serializers.JSONField(source="content", read_only=True)
    title = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    detail_url = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = [
            "id",
            "title",
            "content",
            "title_i18n",
            "content_i18n",
            "published_date",
            "views_count",
            "detail_url",
        ]

    def _get_language_code(self):
        request = self.context.get("request")
        supported_langs = {code for code, _ in settings.LANGUAGES}
        default_lang = settings.LANGUAGE_CODE

        if not request:
            return default_lang

        candidates = [
            request.query_params.get("lang"),
            request.COOKIES.get("selected_language"),
            request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME),
            getattr(request, "LANGUAGE_CODE", None),
        ]

        for candidate in candidates:
            if not candidate:
                continue
            normalized = candidate.split("-")[0].lower()
            if normalized in supported_langs:
                return normalized

        return default_lang

    def _localized_value(self, data):
        if not isinstance(data, dict):
            return data

        lang_code = self._get_language_code()
        return data.get(lang_code) or data.get("uz") or next(iter(data.values()), "")

    def get_title(self, obj):
        return self._localized_value(obj.title)

    def get_content(self, obj):
        return self._localized_value(obj.content)

    def get_detail_url(self, obj):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(f"/v1/announcements/{obj.id}/")
        return f"/v1/announcements/{obj.id}/"


class MedicalCheckupApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalCheckupApplication
        fields = ['full_name', 'phone_number', 'message']
