from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.models import Group, Permission
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView

from apps.medical.models import SiteSettings, MainPageBanner, DoctorAInfo, ContactPhone
from members.models import CustomUser




class UsersView(TemplateView):
    template_name = "users.html"  # template nomini to'g'ri ko'rsating

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # TemplateLayout o'rniga super() dan foydalanish

        # Qidiruv va filter parametrlari
        search_query = self.request.GET.get("search", "").strip()
        filter_department = self.request.GET.get("department", "").strip()
        filter_status = self.request.GET.get("status", "").strip()

        # Foydalanuvchilarni filterlash
        users = self._filter_users(search_query, filter_department, filter_status)

        # Sahifalash (Pagination)
        users_paginated = self._paginate_users(users)

        context["users"] = users_paginated
        context["departments"] = CustomUser.objects.values_list("department", flat=True).distinct()
        return context

    def _filter_users(self, search_query, filter_department, filter_status):
        users = CustomUser.objects.all()

        if search_query:
            users = users.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(full_name__icontains=search_query) |
                Q(phone_number__icontains=search_query)
            )

        if filter_department:
            users = users.filter(department=filter_department)

        if filter_status:
            users = users.filter(is_active=(filter_status == "active"))

        return users

    def _paginate_users(self, users):
        paginator = Paginator(users, 10)
        page = self.request.GET.get("page")
        return paginator.get_page(page)



class HasGroupView(TemplateView):
    template_name = "roles.html"  # template nomini to'g'ri ko'rsating

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # TemplateLayout o'rniga super() dan foydalanish

        # Foydalanuvchi guruhlari va ruxsatlari
        if self.request.user.is_authenticated:
            context["user_groups"] = list(self.request.user.groups.values_list('name', flat=True))
            context["user_permissions"] = list(self.request.user.user_permissions.values_list('name', flat=True))
        else:
            context["user_groups"] = []
            context["user_permissions"] = []

        # Barcha guruhlar, foydalanuvchilar va ruxsatlar
        context["groups"] = Group.objects.all()
        context["users"] = CustomUser.objects.all()
        context["permissions"] = Permission.objects.all()

        return context

    def post(self, request):
        action = request.POST.get("action")

        if action == "create_group":
            self._create_group(request)
        elif action == "add_user_to_group":
            self._add_user_to_group(request)
        elif action == "add_permission_to_group":
            self._add_permission_to_group(request)

        return redirect("roles-page")

    def _create_group(self, request):
        group_name = request.POST.get("group_name")
        if group_name:
            Group.objects.create(name=group_name)
            messages.success(request, f"✅ '{group_name}' guruhi yaratildi!")
        else:
            messages.error(request, "⚠️ Guruh nomi bo'sh bo'lishi mumkin emas!")

    def _add_user_to_group(self, request):
        group_id = request.POST.get("group_id")
        user_id = request.POST.get("user_id")
        group = get_object_or_404(Group, id=group_id)
        user = get_object_or_404(CustomUser, id=user_id)
        group.user_set.add(user)
        messages.success(request, f"✅ {user.username} {group.name} guruhiga qo'shildi!")

    def _add_permission_to_group(self, request):
        group_id = request.POST.get("group_id")
        permission_id = request.POST.get("permission_id")
        group = get_object_or_404(Group, id=group_id)
        permission = get_object_or_404(Permission, id=permission_id)
        group.permissions.add(permission)
        messages.success(request, f"✅ '{permission.name}' ruxsati {group.name} guruhiga qo'shildi!")

class SettingsView(TemplateView):
    template_name = "settings.html"  # template nomini to'g'ri ko'rsating

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # context ni to'g'ri yaratish

        context["site_settings"] = SiteSettings.objects.first()
        context["banners"] = MainPageBanner.objects.all()
        context["doctor_infos"] = DoctorAInfo.objects.all()
        context["contact_phones"] = ContactPhone.objects.all()

        return context

    def post(self, request):
        action = request.POST.get("action")

        if action == "update_settings":
            site_settings = SiteSettings.objects.first()
            if not site_settings:
                site_settings = SiteSettings()

            site_settings.site_name = request.POST.get("site_name")
            site_settings.contact_email = request.POST.get("contact_email")
            site_settings.contact_phone = request.POST.get("contact_phone")
            site_settings.address = request.POST.get("address")
            site_settings.maintenance_mode = "maintenance_mode" in request.POST
            site_settings.facebook_url = request.POST.get("facebook_url")
            site_settings.twitter_url = request.POST.get("twitter_url")
            site_settings.instagram_url = request.POST.get("instagram_url")
            site_settings.linkedin_url = request.POST.get("linkedin_url")

            if "logo_dark" in request.FILES:
                site_settings.logo_dark = request.FILES["logo_dark"]

            if "logo_light" in request.FILES:
                site_settings.logo_light = request.FILES["logo_light"]

            site_settings.save()
            messages.success(request, "Sayt sozlamalari yangilandi!")

        elif action == "add_banner":
            banner = MainPageBanner(image=request.FILES.get("banner_image"), description={"uz": request.POST.get("banner_description")})
            banner.save()
            messages.success(request, "Banner muvaffaqiyatli qo‘shildi!")

        elif action == "delete_banner":
            banner = get_object_or_404(MainPageBanner, id=request.POST.get("banner_id"))
            banner.delete()
            messages.success(request, "Banner o‘chirildi!")

        elif action == "add_doctor_info":
            doctor_info = DoctorAInfo(
                title={"uz": request.POST.get("doctor_title")},
                description={"uz": request.POST.get("doctor_description")},
                image=request.FILES.get("doctor_image")
            )
            doctor_info.save()
            messages.success(request, "Doctor A haqida ma’lumot qo‘shildi!")

        elif action == "delete_doctor_info":
            doctor_info = get_object_or_404(DoctorAInfo, id=request.POST.get("doctor_info_id"))
            doctor_info.delete()
            messages.success(request, "Doctor A haqida ma’lumot o‘chirildi!")

        elif action == "add_contact_phone":
            phone = ContactPhone(phone_number=request.POST.get("phone_number"), description={"uz": request.POST.get("phone_description")})
            phone.save()
            messages.success(request, "Aloqa telefoni qo‘shildi!")

        elif action == "delete_contact_phone":
            phone = get_object_or_404(ContactPhone, id=request.POST.get("phone_id"))
            phone.delete()
            messages.success(request, "Telefon raqami o‘chirildi!")

        return redirect("settings-page-url")  # settings-page-url ni to'g'ri ko'rsating