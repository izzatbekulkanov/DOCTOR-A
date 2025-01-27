from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import static
from core import settings
from django.views.static import serve

from core.views import home_redirect

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),  # Tilni tanlash uchun
    path('', home_redirect, name='home-redirect'),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('account/', include('account.urls')),
    path('', include('dashboard.urls')),
    path('admin-page/', include('medical.urls')),
    path('logs/', include('logs.urls')),
    # Additional patterns go here
)

# Only serve static and media files in DEBUG mode
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
