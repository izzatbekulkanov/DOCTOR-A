# Generated by Django 5.0.6 on 2025-02-25 08:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('medical', '0003_rename_linkedin_url_sitesettings_telegram_url_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='working_hours',
            field=models.CharField(blank=True, help_text='Ish vaqti (masalan: Dushanba - Juma 9:00 - 17:00)', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='telegram_url',
            field=models.URLField(blank=True, help_text='Telegram sahifa URL', null=True),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='youtube_url',
            field=models.URLField(blank=True, help_text='YouTube sahifa URL', null=True),
        ),
    ]
