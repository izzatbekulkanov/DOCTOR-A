from django.urls import path
from .views import NewsView, AddNewsView, NewsDetailView, SetSelectedNewsView, NewsDeleteView, AnnouncementView, \
    AnnouncementCreateView, toggle_news_status
from django.contrib.auth.decorators import login_required

from ..medical.views import PartnerInfoView, get_partner_info

viewspatterns = [
    path("news-view", login_required(NewsView.as_view()), name="news-view", ),
    path("add-news-view", login_required(AddNewsView.as_view()), name="add-news-view", ),
    path("news-detail", NewsDetailView.as_view(), name="news-detail"),  # ID yo‘q
    path("set-selected-news", SetSelectedNewsView.as_view(), name="set-selected-news"),
    # ✅ Yangilikni sessionga saqlash
    path("news-delete", NewsDeleteView.as_view(), name="news-delete"),

    path("announcemen-view", login_required(AnnouncementView.as_view()), name="announcemen-view", ),
    path("announcement-create", AnnouncementCreateView.as_view(), name="announcement-create"),

    path("partners", login_required(PartnerInfoView.as_view()), name="partners-info", ),
    path("get-partner-info", get_partner_info, name="get-partner-info"),
    path("toggle-status/<int:news_id>/", toggle_news_status, name="toggle_news_status"),
]

urlpatterns = viewspatterns
