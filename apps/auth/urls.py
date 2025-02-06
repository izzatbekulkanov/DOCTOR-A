from django.urls import path
from .login.views import LoginView
from .logout.logout import LogoutView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),

    path("logout/",LogoutView.as_view(),name="logout",),

]
