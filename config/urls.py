from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import set_language
from django.views.defaults import page_not_found, permission_denied, bad_request, server_error
from django.views.static import serve
from django.urls import re_path

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
handler404 = "apps.core.views.custom_404"
handler403 = "apps.core.views.custom_403"
handler400 = "apps.core.views.custom_400"
handler500 = "apps.core.views.custom_500"

# 📌 Production muhitida Media va Static fayllarni xizmat qilish
if not settings.DEBUG:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
        re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
    ]
