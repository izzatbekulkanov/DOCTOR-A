from django.shortcuts import render
from django.views.generic import ListView
from ..models import News
from django.utils.translation import gettext_lazy as _

class NewsListView(ListView):
    template_name = 'administrator/views/news.html'
    context_object_name = 'page_obj'
    paginate_by = 10

    def get_queryset(self):
        queryset = News.objects.all().order_by('-created_at')
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(title__icontains=q)
        return queryset

# Tillar ro'yxati
LANGUAGES = [
    ('uz', _('Uzbek')),
    ('kk', _('Kazakh')),
    ('tr', _('Turkish')),
    ('ru', _('Russian')),
    ('en', _('English')),
    ('de', _('German')),
    ('fr', _('French')),
    ('ko', _('Korean')),
]

class AddNewsListView(ListView):
    template_name = 'administrator/views/add-news.html'
    context_object_name = 'page_obj'
    paginate_by = 10

    def get_queryset(self):
        queryset = News.objects.all().order_by('-created_at')
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(title__icontains=q)
        return queryset
