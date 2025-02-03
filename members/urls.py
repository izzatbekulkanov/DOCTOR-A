from django.urls import path
from .views import UsersView, HasGroupView, SettingsView
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path("users-page",login_required(UsersView.as_view(template_name="users.html")),name="users",),
    path("roles-page",login_required(HasGroupView.as_view(template_name="roles.html")),name="roles-page",),
    path("settings-page",login_required(SettingsView.as_view(template_name="settings.html")),name="settings-page-url",),
]
