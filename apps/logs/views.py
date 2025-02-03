from django.core.paginator import Paginator
from django.views.generic import TemplateView

from apps.logs.models import Log



class LogsView(TemplateView):
    # Predefined function
    def get_context_data(self, **kwargs):
        context = (self, super().get_context_data(**kwargs))

        # 📌 Barcha loglarni olish (so‘nggi 1000 log bilan cheklash)
        logs = Log.objects.order_by("-timestamp")[:1000]

        # 📌 Sahifalash (Pagination) - Har 20 ta log bir sahifada
        paginator = Paginator(logs, 20)
        page = self.request.GET.get("page")
        logs_paginated = paginator.get_page(page)

        return context
