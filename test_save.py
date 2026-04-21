import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from apps.members.models import CustomUser
from datetime import date

c = Client()
admin = CustomUser.objects.filter(is_superuser=True).first()
if not admin:
    print("No superuser found.")
    exit(1)

c.force_login(admin)
u = CustomUser.objects.get(id=13)
print(f"Testing save on user {u.id}...")

post_data = {
    'full_name': u.full_name or 'Test User',
    'phone_number': u.phone_number or '+998901234567',
    'gender': u.gender or 'male',
    'bio': '<p>Test bio</p>',
    'username': u.username,
}

response = c.post(f'/administrator/users/edit/{u.id}/', data=post_data, HTTP_HOST='127.0.0.1')
print(f"Status Code: {response.status_code}")
if response.status_code == 302:
    print(f"Redirect URL: {response.url}")
    # Let's check if the bio saved
    u.refresh_from_db()
    print(f"Saved bio: {u.bio}")
else:
    print("Error or form re-render.")
