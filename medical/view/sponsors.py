from django.shortcuts import render
from django.views import View

# Create your views here.
class SponsorsView(View):
    template_name = 'administrator/views/sponsors.html'

    def get(self, request):
        return render(request, self.template_name)