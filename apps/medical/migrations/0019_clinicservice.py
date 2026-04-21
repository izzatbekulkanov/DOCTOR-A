from django.db import migrations, models


def seed_clinic_services(apps, schema_editor):
    ClinicService = apps.get_model("medical", "ClinicService")

    if ClinicService.objects.exists():
        return

    services = [
        {
            "title": {
                "uz": "Ichki kasalliklar",
                "en": "Medicine",
            },
            "summary": {
                "uz": "Kundalik qabul, tashxis va davolash jarayonlarini bir joyda boshqaradigan umumiy terapevtik xizmatlar.",
                "en": "Comprehensive internal medicine support for routine care, diagnostics, and long-term care planning.",
            },
            "icon_class": "flaticon-medicine",
            "sort_order": 10,
            "is_active": True,
        },
        {
            "title": {
                "uz": "Nevrologiya",
                "en": "Neurology",
            },
            "summary": {
                "uz": "Bosh og'rig'i, asab tizimi muammolari va tiklanish jarayonlari uchun mutaxassis korigi va nazorat.",
                "en": "Specialized neurological assessment for headaches, neuropathy, recovery monitoring, and brain health support.",
            },
            "icon_class": "flaticon-neurology",
            "sort_order": 20,
            "is_active": True,
        },
        {
            "title": {
                "uz": "Koz diagnostikasi",
                "en": "Eye Care",
            },
            "summary": {
                "uz": "Korish holatini baholash, skrining va keyingi yonaltirish uchun ko'z tekshiruvlari.",
                "en": "Preventive and diagnostic eye care with structured screening, examination, and referral pathways.",
            },
            "icon_class": "flaticon-eye",
            "sort_order": 30,
            "is_active": True,
        },
        {
            "title": {
                "uz": "Kardiologiya",
                "en": "Cardiology",
            },
            "summary": {
                "uz": "Yurak faoliyatini tekshirish, konsultatsiya va muntazam monitoring uchun kardiologik xizmatlar.",
                "en": "Cardiac consultation, ECG-based evaluation, and monitoring support for ongoing cardiovascular care.",
            },
            "icon_class": "flaticon-heart",
            "sort_order": 40,
            "is_active": True,
        },
        {
            "title": {
                "uz": "Stomatologiya",
                "en": "Dental Care",
            },
            "summary": {
                "uz": "Profilaktika, davolash va keyingi nazoratni qamrab oluvchi stomatologik yordam.",
                "en": "Oral health services covering preventive dentistry, treatment planning, and follow-up visits.",
            },
            "icon_class": "flaticon-dental-care",
            "sort_order": 50,
            "is_active": True,
        },
        {
            "title": {
                "uz": "Pulmonologiya",
                "en": "Pulmonary",
            },
            "summary": {
                "uz": "Nafas yollari bilan bog'liq holatlar uchun tekshiruv, maslahat va muntazam nazorat.",
                "en": "Respiratory assessment and pulmonary care for chronic breathing conditions and recovery support.",
            },
            "icon_class": "flaticon-lungs",
            "sort_order": 60,
            "is_active": True,
        },
    ]

    for service in services:
        ClinicService.objects.create(**service)


class Migration(migrations.Migration):

    dependencies = [
        ("medical", "0018_alter_sitesettings_working_hours"),
    ]

    operations = [
        migrations.CreateModel(
            name="ClinicService",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.JSONField(default=dict, help_text="Har xil tillarda xizmat nomi (JSON formatda)")),
                ("summary", models.JSONField(default=dict, help_text="Har xil tillarda xizmat tavsifi (JSON formatda)")),
                (
                    "icon_class",
                    models.CharField(
                        choices=[
                            ("flaticon-ambulance", "Ambulance"),
                            ("flaticon-brain", "Brain"),
                            ("flaticon-capsules", "Capsules"),
                            ("flaticon-cardiogram", "Cardiogram"),
                            ("flaticon-conference", "Conference"),
                            ("flaticon-dental-care", "Dental Care"),
                            ("flaticon-doctor", "Doctor"),
                            ("flaticon-eye", "Eye"),
                            ("flaticon-first-aid-kit", "First Aid Kit"),
                            ("flaticon-heart", "Heart"),
                            ("flaticon-heart-rate", "Heart Rate"),
                            ("flaticon-kidney", "Kidney"),
                            ("flaticon-kidneys", "Kidneys"),
                            ("flaticon-lungs", "Lungs"),
                            ("flaticon-medicine", "Medicine"),
                            ("flaticon-neurology", "Neurology"),
                            ("flaticon-personal-information", "Personal Information"),
                            ("flaticon-pills", "Pills"),
                            ("flaticon-rate", "Rate"),
                            ("flaticon-scissors", "Scissors"),
                            ("flaticon-stethoscope", "Stethoscope"),
                            ("flaticon-tooth", "Tooth"),
                            ("flaticon-tooth-1", "Tooth Variant"),
                            ("flaticon-user-experience", "User Experience"),
                            ("flaticon-wheelchair", "Wheelchair"),
                        ],
                        default="flaticon-medicine",
                        help_text="Xizmat uchun flaticon klassini tanlang",
                        max_length=64,
                    ),
                ),
                ("sort_order", models.PositiveIntegerField(default=0, help_text="Xizmat ko'rinish tartibi")),
                ("is_active", models.BooleanField(default=True, help_text="Xizmat faol yoki faol emas")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Xizmat",
                "verbose_name_plural": "Xizmatlar",
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.RunPython(seed_clinic_services, migrations.RunPython.noop),
    ]
