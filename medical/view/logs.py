from django.shortcuts import render
from django.views import View

# Create your views here.
class LogsView(View):
    template_name = 'administrator/views/logs.html'

    def get(self, request):
        return render(request, self.template_name)