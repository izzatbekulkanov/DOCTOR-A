from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    full_name = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')], blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)

    # ✅ Klinikaga tegishli maydonlar
    job_title = models.CharField(max_length=100, blank=True, help_text="Lavozim")
    department = models.CharField(max_length=100, blank=True, help_text="Bo'lim")
    employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="Xodim ID")
    employment_date = models.DateField(null=True, blank=True, help_text="Ish boshlash sanasi")
    contract_end_date = models.DateField(null=True, blank=True, help_text="Shartnoma tugash sanasi")
    is_active_employee = models.BooleanField(default=True, help_text="Faol xodimmi?")
    medical_specialty = models.CharField(max_length=100, blank=True, help_text="Tibbiyot mutaxassisligi")
    professional_license_number = models.CharField(max_length=100, blank=True, help_text="Litsenziya raqami")
    shift_schedule = models.CharField(max_length=100, blank=True, help_text="Ish jadvali")

    # ✅ Qo‘shimcha maydonlar
    bank_account_number = models.CharField(max_length=50, blank=True, help_text="Bank hisob raqami")
    tax_identification_number = models.CharField(max_length=20, blank=True, help_text="STIR")
    insurance_number = models.CharField(max_length=50, blank=True, help_text="Sug'urta raqami")

    # ✅ Django standart maydonlari
    is_active = models.BooleanField(default=True, help_text="Foydalanuvchi faol yoki faol emas")
    is_staff = models.BooleanField(default=False, help_text="Admin sahifasiga kira oladimi?")

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if not self.full_name and self.first_name and self.last_name:
            self.full_name = f"{self.first_name} {self.last_name}"
        super().save(*args, **kwargs)