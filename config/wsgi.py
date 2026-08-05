import traceback
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

print(">>> WSGI START")

try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    print(">>> WSGI LOADED")
except Exception:
    traceback.print_exc()
    raise