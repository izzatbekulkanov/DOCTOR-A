from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.urls import path


class DashboardsView(TemplateView):
    template_name = "views/main-dashboard.html"

    # Predefined function
    def get_context_data(self, **kwargs):
        # To'g'ri context olish
        context = super().get_context_data(**kwargs)
        return context  # ❌ Tuple emas, ✅ Dict qaytarish kerak


urlpatterns = [
    path("", login_required(DashboardsView.as_view()), name="main-dashboard"),
]
