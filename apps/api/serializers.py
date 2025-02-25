from rest_framework import serializers

from apps.medical.models import News


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['id', 'title', 'content', 'image', 'published_date', 'views_count']
