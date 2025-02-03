from django.urls import path
from django.contrib.auth.views import LogoutView
from .login.views import LoginView



urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),

    path("logout/",LogoutView.as_view(),name="logout",),

]
