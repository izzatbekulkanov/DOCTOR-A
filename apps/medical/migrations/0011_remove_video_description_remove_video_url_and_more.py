# Generated by Django 5.0.6 on 2025-03-06 10:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('medical', '0010_video'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='video',
            name='description',
        ),
        migrations.RemoveField(
            model_name='video',
            name='url',
        ),
        migrations.AddField(
            model_name='video',
            name='embed_url',
            field=models.URLField(default=1, help_text='YouTube embed URL (masalan, https://www.youtube.com/embed/VIDEO_ID)', max_length=255),
            preserve_default=False,
        ),
    ]
