from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models


class CustomUser(AbstractUser):
    full_name = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)  # Ism
    second_name = models.CharField(max_length=100, null=True, blank=True)  # Familiya
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')], null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    emergency_contact = models.CharField(max_length=15, null=True, blank=True)

    # Klinikaga tegishli maydonlar
    job_title = models.CharField(max_length=100, null=True, blank=True,
                                 help_text="Lavozim, masalan: Shifokor, Hamshira, Administrator")
    department = models.CharField(max_length=100, null=True, blank=True,
                                  help_text="Bo'lim, masalan: Kardiologiya, Pediatriya")
    employee_id = models.CharField(max_length=50, unique=True, null=True, blank=True,
                                   help_text="Xodimning unikal identifikatori")
    employment_date = models.DateField(null=True, blank=True, help_text="Ishga qabul qilingan sana")
    contract_end_date = models.DateField(null=True, blank=True, help_text="Shartnoma tugash sanasi")
    is_active_employee = models.BooleanField(default=True, help_text="Faol xodimmi yoki yo'qmi")
    medical_specialty = models.CharField(max_length=100, null=True, blank=True,
                                         help_text="Tibbiyot sohasidagi mutaxassislik, masalan: Nevrologiya")
    professional_license_number = models.CharField(max_length=100, null=True, blank=True,
                                                   help_text="Mutaxassisning litsenziya raqami")
    shift_schedule = models.CharField(max_length=100, null=True, blank=True,
                                      help_text="Ish jadvali, masalan: 9:00 - 18:00")

    # Qo'shimcha maydonlar
    bank_account_number = models.CharField(max_length=50, null=True, blank=True, help_text="Bank hisob raqami")
    tax_identification_number = models.CharField(max_length=20, null=True, blank=True, help_text="STIR")
    insurance_number = models.CharField(max_length=50, null=True, blank=True, help_text="Sug'urta raqami")

    # Django standart maydonlarini qayta belgilash
    is_active = models.BooleanField(default=True, help_text="Foydalanuvchi faol yoki faol emasligini belgilaydi")
    is_staff = models.BooleanField(default=False, help_text="Foydalanuvchi admin sahifasiga kira oladimi")

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if not self.full_name and self.first_name and self.second_name:
            self.full_name = f"{self.first_name} {self.second_name}"
        super().save(*args, **kwargs)