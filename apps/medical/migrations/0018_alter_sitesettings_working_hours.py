from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("medical", "0017_alter_medicalcheckupapplication_phone_number"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sitesettings",
            name="working_hours",
            field=models.TextField(
                blank=True,
                help_text="Ish vaqti (masalan: Dushanba - Juma 9:00 - 17:00)",
                null=True,
            ),
        ),
    ]
