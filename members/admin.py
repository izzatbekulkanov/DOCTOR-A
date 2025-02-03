from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from members.models import CustomUser


# Register your models here.
# ✅ CustomUser modelini admin panelga qo‘shish
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "is_superuser", "gender", "date_joined")
    fieldsets = (
        (_("Asosiy ma'lumotlar"), {"fields": ("username", "email", "password")}),
        (_("Shaxsiy ma'lumotlar"), {"fields": ("first_name", "last_name", "full_name", "phone_number", "profile_picture")}),
        (_("Qo'shimcha ma'lumotlar"), {"fields": ("nationality", "bio", "gender", "date_of_birth")}),
        (_("Xavfsizlik"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Tizim ma'lumotlari"), {"fields": ("last_login", "date_joined")}),
    )
    search_fields = ("username", "email", "full_name", "phone_number")
    ordering = ("date_joined",)


admin.site.register(CustomUser, CustomUserAdmin)

# ✅ **Admin panel sarlavhasini o‘zgartirish**
admin.site.site_header = "Doctor A - Admin Panel"
admin.site.site_title = "Doctor A"
admin.site.index_title = "Boshqaruv paneli"