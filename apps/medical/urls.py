from django.urls import path
from .views import MainView, MainPageBannerView, get_banner, delete_banner, \
    ContactPhoneView, get_contact_phone, UsersView, RolesView, LogsView, AddUsersView, AppointmentView, EditUsersView, \
    AppointmentDetailView, MedicalCheckupApplicationDetailView, MedicalCheckupApplicationView, MainSettingsView, ClinicEquipmentView, \
    ClientEquipmentDetailView, VideoListView, ServiceListView, ServiceCreateView, ServiceEditView
from django.contrib.auth.decorators import login_required
from apps.bot.views import BotControlView, BotFileProxyView, BotWorkerStatusView

viewspatterns = [
    path("", login_required(MainView.as_view()), name="admin-index", ),
    path("settings", login_required(MainSettingsView.as_view()), name="admin-setting-index", ),
    path("bot", login_required(BotControlView.as_view()), name="bot-control"),
    path("bot/status", login_required(BotWorkerStatusView.as_view()), name="bot-worker-status"),
    path("bot/file/<int:pk>/", login_required(BotFileProxyView.as_view()), name="bot-file-proxy"),
    path("page-banner", login_required(MainPageBannerView.as_view()), name="page-banner", ),

    path('get-banner/<int:banner_id>/', get_banner, name="get_banner"),
    path('delete-banner/<int:banner_id>/', delete_banner, name="delete_banner"),
    path("contact-phone", login_required(ContactPhoneView.as_view()), name="contact-phone", ),
    path("get-contact-phone", get_contact_phone, name="get-contact-phone"),  # GET uchun API

]

havsizlikpatterns = [
    path("users", login_required(UsersView.as_view()), name="users-view", ),
    path("add-users", login_required(AddUsersView.as_view()), name="add-users-view"),
    path('users/edit/<int:user_id>/', EditUsersView.as_view(), name='edit-user'),  # EditUsersView uchun

    path("roles", login_required(RolesView.as_view()), name="roles-view", ),
    path("logs", login_required(LogsView.as_view()), name="logs-view", ),
    path("appointmentView", login_required(AppointmentView.as_view()), name="appointment-view", ),
    path("appointmentView/<int:pk>/", login_required(AppointmentDetailView.as_view()), name="appointment-detail"),

    path('checkup-applications', login_required(MedicalCheckupApplicationView.as_view()), name='medical-checkup-applications'),
    path(
        'checkup-applications/<int:pk>/',
        login_required(MedicalCheckupApplicationDetailView.as_view()),
        name='medical-checkup-application-detail',
    ),
    path('clinic/equipment/', ClinicEquipmentView.as_view(), name='clinic-equipment'),
    path('equipment/<int:pk>/', ClientEquipmentDetailView.as_view(), name='client-equipment-detail'),

    path('videos/', VideoListView.as_view(), name='video-list'),
    path('services/', ServiceListView.as_view(), name='service-list'),
    path('services/create/', ServiceCreateView.as_view(), name='service-create'),
    path('services/edit/<int:service_id>/', ServiceEditView.as_view(), name='service-edit'),
]

urlpatterns = viewspatterns + havsizlikpatterns
