import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.accounts.api import google_login
from apps.accounts.schemas import GoogleLoginSchema
from apps.accounts.models import User

# Delete any existing mock user first to simulate registration
User.objects.filter(email="mock_test@example.com").delete()

class DummyRequest:
    pass

# Try registration with empty fields
payload = GoogleLoginSchema(
    id_token="mock_test",
    action="register",
    gender="FEMALE",
    register_for="SELF",
    date_of_birth=None,
    phone=None
)

try:
    print("Testing registration...")
    res = google_login(DummyRequest(), payload)
    print("Response:", res)
except Exception as e:
    import traceback
    traceback.print_exc()
