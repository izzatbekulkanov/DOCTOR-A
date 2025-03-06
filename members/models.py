from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator


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


class EmployeeActivityHistory(models.Model):
    # Foydalanuvchi bilan bog‘lash
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='activity_history',
        help_text=_("Faoliyat bilan bog‘liq xodim")
    )

    # Faoliyat umumiy ma'lumotlari
    activity_name = models.CharField(
        max_length=255,
        help_text=_("Faoliyat nomi (masalan, 'Operatsiya', 'Malaka oshirish', 'Xizmat safari')")
    )
    activity_type = models.CharField(
        max_length=50,
        choices=[
            ('training', 'Malaka oshirish'),
            ('operation', 'Operatsiya'),
            ('business_trip', 'Xizmat safari'),
            ('certification', 'Sertifikat olish'),
            ('conference', 'Konferensiya'),
            ('workshop', 'Amaliy mashg‘ulot'),
            ('other', 'Boshqa')
        ],
        default='training',
        help_text=_("Faoliyat turi")
    )
    description = models.TextField(
        blank=True,
        help_text=_("Faoliyat haqida qisqacha tavsif (masalan, 'Appendektomiya operatsiyasi', 'Kardiologiya kursi')")
    )

    # Joylashuv ma'lumotlari
    location_name = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Faoliyat joyi (masalan, 'Toshkent Tibbiyot Akademiyasi', 'Parij klinikasi')")
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Shahar (masalan, 'Toshkent', 'Parij')")
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Davlat (masalan, 'O‘zbekiston', 'Fransiya')")
    )

    # Sana va muddat
    start_date = models.DateField(
        help_text=_("Faoliyat boshlanish sanasi")
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Faoliyat tugash sanasi (agar davomiy bo‘lmasa)")
    )

    # Natija va hujjatlar
    is_completed = models.BooleanField(
        default=False,
        help_text=_("Faoliyat muvaffaqiyatli yakunlanganmi?")
    )
    result_details = models.TextField(
        blank=True,
        help_text=_("Natija haqida qo‘shimcha ma'lumot (masalan, 'Sertifikat olindi', 'Operatsiya muvaffaqiyatli')")
    )
    certificate_file = models.FileField(
        upload_to='activity_certificates/',
        blank=True,
        null=True,
        help_text=_("Sertifikat yoki tasdiqlovchi hujjat (PDF, JPG va h.k.)")
    )
    additional_files = models.FileField(
        upload_to='activity_documents/',
        blank=True,
        null=True,
        help_text=_("Qo‘shimcha hujjatlar (masalan, hisobot, fotosurat)")
    )

    # Xarajat va moliyaviy ma'lumotlar
    cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_("Faoliyat xarajati (so‘mda yoki boshqa valyutada)")
    )
    funded_by_clinic = models.BooleanField(
        default=False,
        help_text=_("Klinika tomonidan moliyalashtirilganmi?")
    )
    expense_report = models.FileField(
        upload_to='expense_reports/',
        blank=True,
        null=True,
        help_text=_("Xarajat hisoboti (agar mavjud bo‘lsa)")
    )

    # Qo‘shimcha ma'lumotlar
    related_operation = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Agar operatsiya bo‘lsa, uning turi (masalan, 'Appendektomiya')")
    )
    supervisor = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Rahbar yoki trener ismi (masalan, 'Dr. Ahmadov')")
    )
    notes = models.TextField(
        blank=True,
        help_text=_("Qo‘shimcha eslatmalar yoki izohlar")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Yozuv yaratilgan sana")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Oxirgi yangilangan sana")
    )

    def __str__(self):
        return f"{self.user.full_name} - {self.activity_name} ({self.start_date})"

    def get_duration(self):
        """ Faoliyat muddatini hisoblash """
        if self.start_date and self.end_date:
            duration = (self.end_date - self.start_date).days
            return f"{duration} kun"
        return "Bir kunlik yoki davomiy"

    def clean(self):
        """ Validatsiya: tugash sanasi boshlanish sanasidan oldin bo‘lmasligi kerak """
        from django.core.exceptions import ValidationError
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError(_("Tugash sanasi boshlanish sanasidan oldin bo‘lishi mumkin emas."))

    class Meta:
        verbose_name = _("Xodim faoliyat tarixi")
        verbose_name_plural = _("Xodim faoliyat tarixlari")
        ordering = ['-start_date']  # Eng yangi faoliyatlar yuqorida ko‘rinadi


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