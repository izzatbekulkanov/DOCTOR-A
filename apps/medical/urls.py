from django.urls import path
from .views import MainView, MainPageBannerView, get_banner, delete_banner, \
    ContactPhoneView, get_contact_phone, UsersView, RolesView, LogsView, AddUsersView, AppointmentView
from django.contrib.auth.decorators import login_required

viewspatterns = [
    path("", login_required(MainView.as_view()), name="admin-index", ),
    path("page-banner", login_required(MainPageBannerView.as_view()), name="page-banner", ),


    path('get-banner/<int:banner_id>/', get_banner, name="get_banner"),
    path('delete-banner/<int:banner_id>/', delete_banner, name="delete_banner"),
    path("contact-phone", login_required(ContactPhoneView.as_view()), name="contact-phone", ),
    path("get-contact-phone", get_contact_phone, name="get-contact-phone"),  # GET uchun API

]

havsizlikpatterns = [
    path("users", login_required(UsersView.as_view()), name="users-view", ),
    path("add-users", login_required(AddUsersView.as_view()), name="add-users-view", ),

    path("logs", login_required(RolesView.as_view()), name="roles-view", ),
    path("roles", login_required(LogsView.as_view()), name="logs-view", ),
    path("appointmentView", login_required(AppointmentView.as_view()), name="appointmentView-view", ),

]

urlpatterns = viewspatterns + havsizlikpatterns
