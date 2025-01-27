from django.urls import path

from logs.views import LogsView
from .view.announcement import AnnouncementView
from .view.data import DataView
from .view.employees import EmployeesView
from .view.news import NewsListView, AddNewsListView
from .view.settings import SettingView, contact_phone_delete
from .view.sponsors import SponsorsView
from .views import MainView

mainpatterns = [
    path('', MainView.as_view(), name='main-view'),
]

settingpatterns = [
    path('settings/settings/', SettingView.as_view(), name='setting-view'),
    path('settings/contact-phone/<int:phone_id>/delete/', contact_phone_delete, name='contact-phone-delete'),
    path('settings/logs/', LogsView.as_view(), name='logs-view'),
    path('settings/data/', DataView.as_view(), name='data-view'),
]
mainurlpatterns = [
    path('main/news/', NewsListView.as_view(), name='news-view'),
    path('main/add-news/', AddNewsListView.as_view(), name='add-news-view'),
    path('main/announcement/', AnnouncementView.as_view(), name='announcement-view'),
    path('main/sponsors/', SponsorsView.as_view(), name='sponsors-view'),
    path('main/employees/', EmployeesView.as_view(), name='employees-view'),
]

urlpatterns = mainpatterns + settingpatterns + mainurlpatterns