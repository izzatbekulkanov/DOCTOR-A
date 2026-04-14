from django.urls import path
from django.views.generic import RedirectView
from .views import DashboardsView, NewsView, AnnouncementView, EmployeeView, VideosView, NewsDetailDashboard, \
    AnnouncementDetailView, EmployeeDetailView, ClinicEquipmentListView, EquipmentDetailView, LandingPageV1View, \
    AboutStyleTwoView, ServicesOverviewView, VideosLandingView, BlogRightSidebarView, AnnouncementRightSidebarView, \
    AnnouncementLandingDetailView, DoctorGridView, ContactStyleTwoView, EquipmentLeftSidebarView, NewsLandingDetailView, \
    DoctorLandingDetailView, EquipmentLandingDetailView
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
    path('equipments/', ClinicEquipmentListView.as_view(), name='equipment_list'),
    path('equipments/<int:pk>/', EquipmentDetailView.as_view(), name='equipment_detail'),

    # 🆕 Yangi landing page (v1) - medic template asosida
    path('v1/', LandingPageV1View.as_view(), name='landing-v1'),
    path('v1/about/', AboutStyleTwoView.as_view(), name='landing-v1-about'),
    path('v1/services/', ServicesOverviewView.as_view(), name='landing-v1-services'),
    path('v1/videos/', VideosLandingView.as_view(), name='landing-v1-videos'),
    path('v1/doctors/', DoctorGridView.as_view(), name='landing-v1-doctors'),
    path('v1/doctors/<int:pk>/', DoctorLandingDetailView.as_view(), name='landing-v1-doctor-detail'),
    path('v1/news/', BlogRightSidebarView.as_view(), name='landing-v1-blog'),
    path('v1/news/<int:pk>/', NewsLandingDetailView.as_view(), name='landing-v1-news-detail'),
    path('v1/announcements/', AnnouncementRightSidebarView.as_view(), name='landing-v1-announcements'),
    path('v1/announcements/<int:pk>/', AnnouncementLandingDetailView.as_view(), name='landing-v1-announcement-detail'),
    path('v1/equipment/', EquipmentLeftSidebarView.as_view(), name='landing-v1-equipment'),
    path('v1/equipment/<int:pk>/', EquipmentLandingDetailView.as_view(), name='landing-v1-equipment-detail'),
    path('v1/contact/', ContactStyleTwoView.as_view(), name='landing-v1-contact'),
    path(
        'v1/blog/',
        RedirectView.as_view(pattern_name='landing-v1-blog', permanent=True),
    ),
    path(
        'v1/about-style-two.html',
        RedirectView.as_view(pattern_name='landing-v1-about', permanent=True),
    ),
    path(
        'v1/blog-right-sidebar.html',
        RedirectView.as_view(pattern_name='landing-v1-blog', permanent=True),
    ),
    path(
        'v1/announcements-right-sidebar.html',
        RedirectView.as_view(pattern_name='landing-v1-announcements', permanent=True),
    ),
    path(
        'v1/doctor-grid.html',
        RedirectView.as_view(pattern_name='landing-v1-doctors', permanent=True),
    ),
    path(
        'v1/contact-style-two.html',
        RedirectView.as_view(pattern_name='landing-v1-contact', permanent=True),
    ),
    path(
        'v1/blog-left-sidebar.html',
        RedirectView.as_view(pattern_name='landing-v1-equipment', permanent=True),
    ),
]
