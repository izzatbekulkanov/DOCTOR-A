from django import forms
from .models import Video
import re

class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['title', 'embed_url', 'is_active']

    def clean_embed_url(self):
        embed_url = self.cleaned_data.get('embed_url')
        match = re.search(Video.YOUTUBE_REGEX, embed_url)
        if not match:
            raise forms.ValidationError("To‘g‘ri YouTube embed URL kiriting!")
        return match.group(1)  # Faqat video ID qaytariladi