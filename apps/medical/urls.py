from django.urls import path
from .views import MainView, MainPageBannerView, get_banner, delete_banner, DoctorAInfoView
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path("",login_required(MainView.as_view()),name="admin-index",),
    path("page-banner",login_required(MainPageBannerView.as_view()),name="page-banner",),
    path("doctor-info",login_required(DoctorAInfoView.as_view()),name="doctor-info",),
    path('get-banner/<int:banner_id>/', get_banner, name="get_banner"),
    path('delete-banner/<int:banner_id>/', delete_banner, name="delete_banner"),

]
