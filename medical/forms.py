from django import forms
from .models import MainPageBanner, DoctorAInfo


class MainPageBannerForm(forms.ModelForm):
    class Meta:
        model = MainPageBanner
        fields = ['image', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Rasm haqida qisqacha tavsif'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'image': 'Banner rasmi',
            'description': 'Tavsif',
        }


class DoctorAInfoForm(forms.ModelForm):
    class Meta:
        model = DoctorAInfo
        fields = ['title', 'description', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sarlavha kiriting'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Batafsil ma\'lumot'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Sarlavha',
            'description': 'Batafsil tavsif',
            'image': 'Rasm',
        }
