from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter

from apps.api.serializers import AnnouncementSerializer
from apps.news.models import Announcement


# 📌 Sahifalash (Pagination) - Har safar 6 ta e'lon chiqarish
class AnnouncementPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = "page_size"

# 📌 API orqali e'lonlarni olish
@method_decorator(ensure_csrf_cookie, name="dispatch")  # ✅ CSRF cookie qo'shish
class AnnouncementListView(ListAPIView):
    serializer_class = AnnouncementSerializer
    pagination_class = AnnouncementPagination
    filter_backends = [SearchFilter]
    search_fields = ['title__uz', 'title__ru', 'title__en']  # 🔎 Har xil tillar uchun qidirish
    queryset = Announcement.objects.filter(is_published=True).order_by("-published_date")

# 📌 API orqali bitta e'lonni olish (detail view)
@method_decorator(ensure_csrf_cookie, name="dispatch")  # ✅ CSRF cookie qo'shish
class AnnouncementDetailView(RetrieveAPIView):
    queryset = Announcement.objects.filter(is_published=True)
    serializer_class = AnnouncementSerializer
    lookup_field = 'pk' # ID bo'yicha qidirish uchun
