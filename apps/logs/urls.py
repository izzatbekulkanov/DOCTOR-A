from django.urls import path
from .views import LogsView
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path("logs-page",login_required(LogsView.as_view(template_name="logs.html")),name="logs-index",),
]
