from django.urls import path
from django.contrib.auth.decorators import login_required

from apps.api.view.checkUp import MedicalCheckupApplicationView
from apps.api.view.news import NewsListView
from apps.api.view.announcements import AnnouncementListView, AnnouncementDetailView

urlpatterns = [
    path('news/', NewsListView.as_view(), name='news-list'),
    path('announcements/', AnnouncementListView.as_view(), name='announcement-list'),
    path('announcements/<int:pk>/', AnnouncementDetailView.as_view(), name='announcement-detail'),
    path('submit-application/', MedicalCheckupApplicationView.as_view(), name='submit_application'),
]
