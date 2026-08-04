import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.accounts.models import User

for u in User.objects.all():
    print(f"ID: {u.id}, Email: {u.email}, Phone: {u.phone}, GoogleID: {u.google_id}, Gender: {u.gender}")
