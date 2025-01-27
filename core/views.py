from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import get_language

def home_redirect(request):
    return HttpResponseRedirect(reverse('dashboard-home'))  # O'zingizning asosiy sahifa yo'nalishingizni o'zgartiring