from django.urls import path
from django.contrib.auth.decorators import login_required

from apps.api.view.news import NewsListView

urlpatterns = [
    path('news/', NewsListView.as_view(), name='news-list'),
]
