from rest_framework import serializers

from apps.medical.models import MedicalCheckupApplication
from apps.news.models import News


class NewsSerializer(serializers.ModelSerializer):
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)

    class Meta:
        model = News
        fields = ['id', 'title', 'content', 'image', 'published_date', 'views_count', 'comments_count']




class MedicalCheckupApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalCheckupApplication
        fields = ['full_name', 'phone_number', 'message']
