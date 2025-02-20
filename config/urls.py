from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import set_language
from django.views.defaults import page_not_found, permission_denied, bad_request, server_error

urlpatterns = [
    path("admin/", admin.site.urls),

    # Dashboard URLs
    path("", include("apps.dashboards.urls")),
    path("", include("apps.news.urls")),

    # Auth URLs
    path("", include("apps.auth.urls")),

    # Medical URLs
    path("administrator/", include("apps.medical.urls")),

    # Members (foydalanuvchilar)
    path("members/", include("members.urls")),

    # Logs
    path("logs/", include("apps.logs.urls")),

    # Til sozlamalari
    path("i18n/set_language/", set_language, name="set_language"),
]

# 📌 Xatolik sahifalarini sozlash
if settings.DEBUG:
    urlpatterns += [
        path("404/", lambda request: page_not_found(request, Exception()), name="error_404"),
        path("403/", lambda request: permission_denied(request, Exception()), name="error_403"),
        path("400/", lambda request: bad_request(request, Exception()), name="error_400"),
        path("500/", lambda request: server_error(request), name="error_500"),
    ]

# 📌 Statik va Media fayllarni xizmat qilish (DEBUG=True holatida)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
