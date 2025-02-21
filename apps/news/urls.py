from django.urls import path
from .views import NewsView, AddNewsView, NewsDetailView, SetSelectedNewsView, NewsDeleteView, AnnouncementView, \
    AnnouncementCreateView
from django.contrib.auth.decorators import login_required

viewspatterns = [
    path("news-view", login_required(NewsView.as_view()), name="news-view", ),
    path("add-news-view", login_required(AddNewsView.as_view()), name="add-news-view", ),
    path("news-detail/", NewsDetailView.as_view(), name="news-detail"),  # ID yo‘q
    path("set-selected-news/", SetSelectedNewsView.as_view(), name="set-selected-news"),
    # ✅ Yangilikni sessionga saqlash
    path("news-delete/", NewsDeleteView.as_view(), name="news-delete"),

    path("announcemen-view", login_required(AnnouncementView.as_view()), name="announcemen-view", ),
    path("announcement-create/", AnnouncementCreateView.as_view(), name="announcement-create"),

]

urlpatterns = viewspatterns
