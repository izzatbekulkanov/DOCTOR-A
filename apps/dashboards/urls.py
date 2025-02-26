from django.urls import path
from .views import DashboardsView, NewsView, AnnouncementView, EmployeeView, VideosView, NewsDetailDashboard, \
    AnnouncementDetailView, EmployeeDetailView
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path("", DashboardsView.as_view(template_name="views/main-dashboard.html"), name="main-dashboard", ),
    path("news/", NewsView.as_view(template_name="views/news-dashboard.html"), name="news-dashboard", ),
    path("news/<int:pk>/", NewsDetailDashboard.as_view(), name="news_detail_dashboard"),  # Yangilik tafsilotlari

    path("announcement/", AnnouncementView.as_view(template_name="views/announcement-dashboard.html"),
         name="announcement-dashboard", ),

    path("announcement/<int:pk>/", AnnouncementDetailView.as_view(), name="announcement_detail"),

    path("employee/", EmployeeView.as_view(template_name="views/employee-dashboard.html"), name="employee-dashboard", ),
    path("employees/<int:pk>/", EmployeeDetailView.as_view(), name="employee_detail"),
    path("videos/", VideosView.as_view(template_name="views/videos-dashboard.html"), name="videos-dashboard", ),
]
