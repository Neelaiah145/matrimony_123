import random
import getpass
from django.core.management.base import BaseCommand
from apps.accounts.models import User, Role, RegisterFor
from django.contrib.auth.hashers import make_password

class Command(BaseCommand):
    help = 'Create a super admin user prompting for Email, First Name, Last Name, and Password only.'

    def handle(self, *args, **options):
        self.stdout.write("Create Matrimony Super Admin:")
        
        email = input("Email: ").strip()
        if not email:
            self.stderr.write("Email is required.")
            return

        if User.objects.filter(email=email).exists():
            self.stderr.write("User with this email already exists.")
            return

        first_name = input("First Name: ").strip()
        last_name = input("Last Name: ").strip()

        password = getpass.getpass("Password: ")
        confirm_password = getpass.getpass("Password (again): ")

        if password != confirm_password:
            self.stderr.write("Passwords do not match.")
            return

        if len(password) < 8:
            self.stderr.write("Password must be at least 8 characters long.")
            return

        # Generate a unique dummy phone number to satisfy database unique constraints
        dummy_phone = "".join([str(random.randint(0, 9)) for _ in range(10)])
        while User.objects.filter(phone=dummy_phone).exists():
            dummy_phone = "".join([str(random.randint(0, 9)) for _ in range(10)])

        role, _ = Role.objects.get_or_create(code="SUPER_ADMIN", defaults={"name": "Super Admin"})
        rf, _ = RegisterFor.objects.get_or_create(id=1, defaults={"name": "SELF"})

        User.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=dummy_phone,
            role=role,
            register_for=rf,
            gender="MALE",
            date_of_birth="1990-01-01",
            password=make_password(password),
            is_staff=True,
            is_superuser=True,
            is_active=True
        )
        
        self.stdout.write(self.style.SUCCESS(f"Super Admin created successfully with Email: {email} and auto-assigned Phone: {dummy_phone}!"))
