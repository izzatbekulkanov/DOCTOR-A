from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.models import Group, Permission
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView

from apps.medical.models import SiteSettings, MainPageBanner, DoctorAInfo, ContactPhone
from members.models import CustomUser