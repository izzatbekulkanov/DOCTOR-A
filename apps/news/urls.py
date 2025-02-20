from django.urls import path
from .views import NewsView, AddNewsView, NewsDetailView
from django.contrib.auth.decorators import login_required

viewspatterns = [
    path("news-view", login_required(NewsView.as_view()), name="news-view", ),
    path("add-news-view", login_required(AddNewsView.as_view()), name="add-news-view", ),
    path("news-detail/", NewsDetailView.as_view(), name="news-detail"),  # ID yo‘q

]

urlpatterns = viewspatterns
