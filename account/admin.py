# account/admin.py
from django.contrib import admin
from .models import CustomUser
from django.contrib.auth.models import Group, Permission

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'full_name', 'email', 'phone_number', 'job_title', 'department', 'is_active_employee'
    )
    list_filter = ('is_active_employee', 'department', 'gender')
    search_fields = ('username', 'full_name', 'email', 'phone_number', 'job_title')
    fieldsets = (
        (None, {
            'fields': ('username', 'password', 'email', 'first_name', 'second_name', 'full_name', 'profile_picture')
        }),
        ('Personal Information', {
            'fields': ('phone_number', 'address', 'date_of_birth', 'gender', 'nationality', 'bio', 'emergency_contact')
        }),
        ('Employment Details', {
            'fields': ('job_title', 'department', 'employee_id', 'employment_date', 'contract_end_date', 'is_active_employee', 'medical_specialty', 'professional_license_number', 'shift_schedule')
        }),
        ('Financial Information', {
            'fields': ('bank_account_number', 'tax_identification_number', 'insurance_number')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
    )
    ordering = ('username',)

admin.site.register(Permission)
