from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter

from apps.api.serializers import NewsSerializer
from apps.news.models import News


# 📌 Sahifalash (Pagination) - Har safar 6 ta yangilik chiqarish
class NewsPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = "page_size"

# 📌 API orqali yangiliklarni olish
@method_decorator(ensure_csrf_cookie, name="dispatch")  # ✅ CSRF cookie qo'shish
class NewsListView(ListAPIView):
    serializer_class = NewsSerializer
    pagination_class = NewsPagination
    filter_backends = [SearchFilter]
    search_fields = ['title__uz', 'title__ru', 'title__en']  # 🔎 Har xil tillar uchun qidirish

    def get_queryset(self):
        queryset = News.objects.filter(is_published=True).order_by('-published_date')

        # 🔎 Oyni bo‘yicha filterlash
        month = self.request.query_params.get('month')
        if month:
            queryset = queryset.filter(published_date__month=month)

        return queryset