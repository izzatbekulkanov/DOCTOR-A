from django.urls import path
from .views import MainView, MainPageBannerView, get_banner, delete_banner, DoctorAInfoView, get_doctor_info, \
    ContactPhoneView, get_contact_phone, UsersView, RolesView, LogsView
from django.contrib.auth.decorators import login_required

viewspatterns = [
    path("", login_required(MainView.as_view()), name="admin-index", ),
    path("page-banner", login_required(MainPageBannerView.as_view()), name="page-banner", ),
    path("doctor-info", login_required(DoctorAInfoView.as_view()), name="doctor-info", ),
    path("get-doctor-info", get_doctor_info, name="get-doctor-info"),

    path('get-banner/<int:banner_id>/', get_banner, name="get_banner"),
    path('delete-banner/<int:banner_id>/', delete_banner, name="delete_banner"),
    path("contact-phone", login_required(ContactPhoneView.as_view()), name="contact-phone", ),
    path("get-contact-phone", get_contact_phone, name="get-contact-phone"),  # GET uchun API

]

havsizlikpatterns = [
    path("users", login_required(UsersView.as_view()), name="users-view", ),

    path("logs", login_required(RolesView.as_view()), name="roles-view", ),
    path("roles", login_required(LogsView.as_view()), name="logs-view", ),

]

urlpatterns = viewspatterns + havsizlikpatterns
