from django.shortcuts import render
from django.views import View

# Create your views here.
class AnnouncementView(View):
    template_name = 'administrator/views/announcement.html'

    def get(self, request):
        return render(request, self.template_name)