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

    # ✅ Ish vaqti
    work_start_time = models.TimeField(null=True, blank=True, help_text="Ish boshlanish vaqti")
    work_end_time = models.TimeField(null=True, blank=True, help_text="Ish tugash vaqti")

    # ✅ Qo‘shimcha maydonlar
    bank_account_number = models.CharField(max_length=50, blank=True, help_text="Bank hisob raqami")
    tax_identification_number = models.CharField(max_length=20, blank=True, help_text="STIR")
    insurance_number = models.CharField(max_length=50, blank=True, help_text="Sug'urta raqami")

    # ✅ Ijtimoiy tarmoqlar
    telegram_username = models.CharField(max_length=100, blank=True, help_text="Telegram foydalanuvchi nomi")
    instagram_username = models.CharField(max_length=100, blank=True, help_text="Instagram foydalanuvchi nomi")

    # ✅ Django standart maydonlari
    is_active = models.BooleanField(default=True, help_text="Foydalanuvchi faol yoki faol emas")
    is_staff = models.BooleanField(default=False, help_text="Admin sahifasiga kira oladimi?")

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if not self.full_name and self.first_name and self.last_name:
            self.full_name = f"{self.first_name} {self.last_name}"
        super().save(*args, **kwargs)

    def get_work_schedule(self):
        """ Ish jadvalini formatda qaytaradi """
        if self.work_start_time and self.work_end_time:
            return f"{self.work_start_time.strftime('%H:%M')} - {self.work_end_time.strftime('%H:%M')}"
        return "Ish vaqti belgilanmagan"


class TrainingHistory(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='training_history')
    training_name = models.CharField(max_length=255, help_text="Malaka oshirish kursining nomi")
    training_date = models.DateField(help_text="Malaka oshirish sanasi")
    certificate_picture = models.ImageField(upload_to='training_certificates/', blank=True, null=True, help_text="Sertifikat rasmi")

    def __str__(self):
        return f"{self.user.full_name} - {self.training_name} ({self.training_date})"

    class Meta:
        verbose_name = "Malaka oshirish tarixi"
        verbose_name_plural = "Malaka oshirish tarixlari"


class Appointment(models.Model):
    """Hodim qabuliga yozilish modeli"""
    full_name = models.CharField(max_length=255, help_text="Foydalanuvchi ismi familiyasi")
    phone_number = models.CharField(max_length=15, help_text="Telefon raqami")
    message = models.TextField(help_text="So‘rov")
    employee = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'is_active_employee': True},  # Faqat faol hodimlar
        related_name="appointments",
        help_text="Qabul qiluvchi hodim"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="Yaratilgan sana")
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Kutilmoqda'),
            ('approved', 'Tasdiqlangan'),
            ('canceled', 'Bekor qilingan')
        ],
        default='pending',
        help_text="Qabul holati"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Qabul"
        verbose_name_plural = "Qabullar"

    def __str__(self):
        return f"{self.full_name} → {self.employee.full_name} ({self.get_status_display()})"