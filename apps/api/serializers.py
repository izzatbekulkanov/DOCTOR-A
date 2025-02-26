from rest_framework import serializers

from apps.medical.models import News, MedicalCheckupApplication


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['id', 'title', 'content', 'image', 'published_date', 'views_count']



class MedicalCheckupApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalCheckupApplication
        fields = ['full_name', 'phone_number', 'message']
