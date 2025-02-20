from django import forms
from apps.medical.models import News
from django.utils.translation import gettext_lazy as _

LANGUAGES = [
    ("uz", _("O'zbek")),
    ("ru", _("Русский")),
    ("en", _("English")),
    ("de", _("Deutsch")),
    ("tr", _("Türkçe")),
]


class NewsForm(forms.ModelForm):
    """ 📰 Ko‘p tilda yangilik formasi """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Har bir til uchun maydonlarni dinamik ravishda qo'shish
        for lang_code, lang_name in LANGUAGES:
            self.fields[f"title_{lang_code}"] = forms.CharField(
                label=f"{lang_name} - Sarlavha",
                widget=forms.TextInput(attrs={'class': 'form-control'}),
                required=False
            )
            self.fields[f"content_{lang_code}"] = forms.CharField(
                label=f"{lang_name} - Matn",
                widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
                required=False
            )
            self.fields[f"image_{lang_code}"] = forms.ImageField(
                label=f"{lang_name} - Rasm",
                required=False,
                widget=forms.FileInput(attrs={'class': 'form-control'})
            )

    class Meta:
        model = News
        fields = []
