from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import ListView, DetailView
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['LANGUAGES'] = LANGUAGES
        return context

    def post(self, request):
        title = {}
        content = {}
        for code, _ in LANGUAGES:
            title[code] = request.POST.get(f'title[{code}]', '')
            content[code] = request.POST.get(f'content[{code}]', '')

        image = request.FILES.get('image')
        published_date = request.POST.get('published_date')
        is_published = 'is_published' in request.POST

        # Validation (Add your validation logic here if needed)
        if not title.get('uz', '').strip():
            return JsonResponse({'status': 'error', 'message': 'O‘zbekcha sarlavha bo‘sh bo‘lishi mumkin emas!'},
                                status=400)

        # Create the news record
        News.objects.create(
            title=title,
            content=content,
            image=image,
            published_date=published_date,
            is_published=is_published
        )

        return JsonResponse({'status': 'success', 'message': 'Yangilik muvaffaqiyatli qo‘shildi!'})

class NewsDetailView(DetailView):
    model = News
    template_name = 'administrator/views/news_detail.html'
    context_object_name = 'news'