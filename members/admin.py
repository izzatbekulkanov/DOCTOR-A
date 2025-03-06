from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Count

from members.models import CustomUser, Appointment, EmployeeActivityHistory

# ✅ Admin panel sarlavhasini o‘zgartirish
admin.site.site_header = "Doctor A - Admin Panel"
admin.site.site_title = "Doctor A"
admin.site.index_title = "Boshqaruv paneli"


# ✅ CustomUser uchun Admin panel
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = (
    "username", "email", "full_name", "phone_number", "gender_display", "is_staff", "is_active", "date_joined",
    "last_login")
    list_filter = ("is_staff", "is_active", "is_superuser", "gender", "date_joined", "last_login")
    search_fields = ("username", "email", "full_name", "phone_number", "bio")
    ordering = ("-date_joined",)
    list_per_page = 25  # Har sahifada 25 ta foydalanuvchi

    # Qo‘shimcha ko‘rsatkichlar uchun metodlar
    def gender_display(self, obj):
        """Jinsni chiroyli ko‘rsatish"""
        return obj.get_gender_display() if obj.gender else "Noma'lum"

    gender_display.short_description = _("Jins")

    # Fieldsets - sozlamalar guruhi
    fieldsets = (
        (_("Asosiy ma'lumotlar"), {"fields": ("username", "email", "password")}),
        (_("Shaxsiy ma'lumotlar"), {
            "fields": ("first_name", "last_name", "full_name", "phone_number", "profile_picture"),
        }),
        (_("Qo'shimcha ma'lumotlar"), {
            "fields": ("nationality", "bio", "gender", "date_of_birth"),
        }),
        (_("Xavfsizlik"), {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
        }),
        (_("Tizim ma'lumotlari"), {
            "fields": ("last_login", "date_joined"),
            "classes": ("collapse",),  # Yashiriladigan qism
        }),
    )

    # Inline qo‘shish: Foydalanuvchi qabullari
    class AppointmentInline(admin.TabularInline):
        model = Appointment
        extra = 0  # Bo‘sh forma qo‘shmaydi
        fields = ('full_name', 'phone_number', 'status', 'created_at')
        readonly_fields = ('created_at',)

    inlines = [AppointmentInline]

    # Custom actions
    def make_active(self, request, queryset):
        """Tanlangan foydalanuvchilarni faol qilish"""
        queryset.update(is_active=True)
        self.message_user(request, _("Tanlangan foydalanuvchilar faol qilindi."))

    make_active.short_description = _("Foydalanuvchilarni faol qilish")

    def make_inactive(self, request, queryset):
        """Tanlangan foydalanuvchilarni nofaol qilish"""
        queryset.update(is_active=False)
        self.message_user(request, _("Tanlangan foydalanuvchilar nofaol qilindi."))

    make_inactive.short_description = _("Foydalanuvchilarni nofaol qilish")

    actions = ['make_active', 'make_inactive']

    # Jadvalda link ko‘rsatish
    def full_name_link(self, obj):
        """Foydalanuvchi nomini link sifatida ko‘rsatish"""
        return format_html('<a href="{}">{}</a>', reverse('admin:members_customuser_change', args=[obj.id]),
                           obj.full_name)

    full_name_link.short_description = _("To‘liq ism")


admin.site.register(CustomUser, CustomUserAdmin)


# ✅ Appointment uchun Admin panel
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'employee_link', 'status_colored', 'created_at', 'action_buttons')
    list_filter = ('status', 'created_at', 'employee__is_active_employee', 'employee__full_name')
    search_fields = ('full_name', 'phone_number', 'message', 'employee__full_name')
    list_per_page = 20  # Har sahifada 20 ta qabul
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'  # Sana bo‘yicha ierarxik filtr

    # Qo‘shimcha metodlar
    def employee_link(self, obj):
        """Hodim nomini link sifatida ko‘rsatish"""
        return format_html('<a href="{}">{}</a>',
                           reverse('admin:members_customuser_change', args=[obj.employee.id]),
                           obj.employee.full_name)

    employee_link.short_description = _("Hodim")

    def status_colored(self, obj):
        """Holatni rangli ko‘rsatish"""
        colors = {
            'pending': 'warning',
            'approved': 'success',
            'canceled': 'danger'
        }
        return format_html('<span class="badge bg-{}">{}</span>', colors.get(obj.status, 'secondary'),
                           obj.get_status_display())

    status_colored.short_description = _("Holat")

    def action_buttons(self, obj):
        """Holatni o‘zgartirish va o‘chirish uchun tugmalar"""
        return format_html(
            '<select onchange="updateStatus(this, \'{}\')" class="form-select form-select-sm d-inline-block w-auto">'
            '<option value="pending" {}>{}</option>'
            '<option value="approved" {}>{}</option>'
            '<option value="canceled" {}>{}</option>'
            '</select> '
            '<button class="btn btn-danger btn-sm ms-2" onclick="deleteAppointment(\'{}\')">O‘chirish</button>',
            obj.id,
            'selected' if obj.status == 'pending' else '', _("Kutilmoqda"),
            'selected' if obj.status == 'approved' else '', _("Tasdiqlangan"),
            'selected' if obj.status == 'canceled' else '', _("Bekor qilingan"),
            obj.id
        )

    action_buttons.short_description = _("Amallar")
    action_buttons.allow_tags = True

    # Custom actions
    def approve_appointments(self, request, queryset):
        """Tanlangan qabullarni tasdiqlash"""
        queryset.update(status='approved')
        self.message_user(request, _("Tanlangan qabullar tasdiqlandi."))

    approve_appointments.short_description = _("Qabullarni tasdiqlash")

    def cancel_appointments(self, request, queryset):
        """Tanlangan qabullarni bekor qilish"""
        queryset.update(status='canceled')
        self.message_user(request, _("Tanlangan qabullar bekor qilindi."))

    cancel_appointments.short_description = _("Qabullarni bekor qilish")

    actions = ['approve_appointments', 'cancel_appointments']

    # JavaScript skriptini admin panelga qo‘shish
    class Media:
        js = (
            'js/admin_appointment.js',  # Quyida keltirilgan JS fayli
        )


# Inline model uchun (agar kerak bo‘lsa)
class EmployeeActivityHistoryInline(admin.TabularInline):
    model = EmployeeActivityHistory
    extra = 1  # Bo‘sh forma soni
    fields = ('activity_name', 'activity_type', 'start_date', 'end_date', 'is_completed')
    readonly_fields = ('created_at', 'updated_at')


# EmployeeActivityHistory uchun admin panel
@admin.register(EmployeeActivityHistory)
class EmployeeActivityHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'user_full_name', 'activity_name', 'activity_type_display', 'start_date', 'end_date',
        'duration_display', 'location_display', 'is_completed_display', 'funded_by_clinic_display',
        'certificate_link'
    )
    list_filter = (
        'activity_type', 'is_completed', 'funded_by_clinic', 'start_date', 'end_date',
        'country', 'city'
    )
    search_fields = (
        'user__full_name', 'activity_name', 'description', 'location_name', 'city',
        'country', 'related_operation', 'supervisor'
    )
    date_hierarchy = 'start_date'  # Sana bo‘yicha navigatsiya
    ordering = ('-start_date',)  # Eng yangi faoliyatlar yuqorida
    list_per_page = 20  # Har sahifada 20 ta yozuv

    # Fieldsets bilan ma'lumotlarni guruhlash
    fieldsets = (
        (_("Asosiy ma'lumotlar"), {
            'fields': ('user', 'activity_name', 'activity_type', 'description')
        }),
        (_("Joylashuv"), {
            'fields': ('location_name', 'city', 'country')
        }),
        (_("Sana va muddat"), {
            'fields': ('start_date', 'end_date')
        }),
        (_("Natija va hujjatlar"), {
            'fields': ('is_completed', 'result_details', 'certificate_file', 'additional_files')
        }),
        (_("Xarajatlar"), {
            'fields': ('cost', 'funded_by_clinic', 'expense_report')
        }),
        (_("Qo‘shimcha ma'lumotlar"), {
            'fields': ('related_operation', 'supervisor', 'notes')
        }),
        (_("Tizim ma'lumotlari"), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)  # Katlanadigan qism
        }),
    )

    # Readonly fields
    readonly_fields = ('created_at', 'updated_at', 'get_duration')

    # Maxsus ko‘rsatuvchi metodlar
    def user_full_name(self, obj):
        return obj.user.full_name
    user_full_name.short_description = _("Xodim nomi")

    def activity_type_display(self, obj):
        return obj.get_activity_type_display()
    activity_type_display.short_description = _("Faoliyat turi")

    def duration_display(self, obj):
        return obj.get_duration()
    duration_display.short_description = _("Muddat")

    def location_display(self, obj):
        parts = [obj.location_name, obj.city, obj.country]
        location = ", ".join(part for part in parts if part)
        return location or "Joy aniqlanmagan"
    location_display.short_description = _("Joylashuv")

    def is_completed_display(self, obj):
        return format_html(
            '<span style="color: {}">{}</span>',
            'green' if obj.is_completed else 'red',
            _("Ha") if obj.is_completed else _("Yo‘q")
        )
    is_completed_display.short_description = _("Yakunlanganmi?")
    is_completed_display.allow_tags = True

    def funded_by_clinic_display(self, obj):
        return format_html(
            '<span style="color: {}">{}</span>',
            'green' if obj.funded_by_clinic else 'grey',
            _("Ha") if obj.funded_by_clinic else _("Yo‘q")
        )
    funded_by_clinic_display.short_description = _("Klinika tomonidan moliyalashtirilganmi?")
    funded_by_clinic_display.allow_tags = True

    def certificate_link(self, obj):
        if obj.certificate_file:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                obj.certificate_file.url,
                _("Sertifikatni ko‘rish")
            )
        return "-"
    certificate_link.short_description = _("Sertifikat")
    certificate_link.allow_tags = True

    # Qo‘shimcha funksiyalar
    def get_queryset(self, request):
        """ Superuser bo‘lmasa, faqat o‘z faoliyatlarini ko‘rsin """
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(user=request.user)
        return qs

    def save_model(self, request, obj, form, change):
        """ Saqlashda qo‘shimcha logika """
        if not change:  # Yangi yozuv qo‘shilganda
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        """ Superuser bo‘lmasa o‘chirishni cheklash """
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        """ Superuser bo‘lmasa faqat o‘z yozuvlarini tahrirlash """
        if obj and not request.user.is_superuser:
            return obj.user == request.user
        return True