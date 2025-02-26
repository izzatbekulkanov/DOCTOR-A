from django.urls import path
from django.contrib.auth.decorators import login_required

from apps.api.view.checkUp import MedicalCheckupApplicationView
from apps.api.view.news import NewsListView

urlpatterns = [
    path('news/', NewsListView.as_view(), name='news-list'),
    path('submit-application/', MedicalCheckupApplicationView.as_view(), name='submit_application'),
]
