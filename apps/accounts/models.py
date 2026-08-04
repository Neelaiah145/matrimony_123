from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Permission
from django.contrib.auth.base_user import BaseUserManager
# Create your models here.



# base models 
class BaseModel(models.Model):
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created_by"
    )

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated_by"
    )

    class Meta:
        abstract = True
        



# role creation model
class Role(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="roles"
    )

    class Meta:
        db_table = "roles"
        ordering = ["id"]

    def __str__(self):
        return self.name



# register for model
class RegisterFor(BaseModel):
    name = models.CharField(
        max_length=50,
        unique=True
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "register_for"
        ordering = ["id"]

    def __str__(self):
        return self.name




class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
            
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        
        is_staff_or_superuser = extra_fields.get("is_staff") or extra_fields.get("is_superuser")
        
        # Only assign safe defaults for regular customers, let staff/superusers have NULLs
        if not is_staff_or_superuser:
            if "role" not in extra_fields:
                from apps.accounts.models import Role
                role, _ = Role.objects.get_or_create(code="CUSTOMER", defaults={"name": "Customer"})
                extra_fields["role"] = role
                
            if "register_for" not in extra_fields:
                from apps.accounts.models import RegisterFor
                rf, _ = RegisterFor.objects.get_or_create(name="SELF")
                extra_fields["register_for"] = rf
                
            if "gender" not in extra_fields:
                extra_fields["gender"] = None
                
            if "date_of_birth" not in extra_fields:
                if extra_fields.get("auth_provider") == "GOOGLE":
                    extra_fields["date_of_birth"] = None
                else:
                    extra_fields["date_of_birth"] = "1990-01-01"

            if "phone" not in extra_fields:
                extra_fields["phone"] = None
        else:
            # Set defaults to None for superusers if not explicitly provided
            extra_fields.setdefault("role", None)
            extra_fields.setdefault("register_for", None)
            extra_fields.setdefault("gender", None)
            extra_fields.setdefault("date_of_birth", None)
            extra_fields.setdefault("phone", None)
            extra_fields.setdefault("auth_provider", None)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        
        # Assign SUPER_ADMIN role to superusers
        from apps.accounts.models import Role
        role, _ = Role.objects.get_or_create(code="SUPER_ADMIN", defaults={"name": "Super Admin"})
        extra_fields["role"] = role

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


# user model
class User(AbstractUser, BaseModel):
    username = None

    GENDER_CHOICES = (
        ("MALE", "Male"),
        ("FEMALE", "Female"),
    )

    AUTH_PROVIDER_CHOICES = (
        ("PHONE", "Phone"),
        ("EMAIL", "Email"),
        ("GOOGLE", "Google"),
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True
    )

    register_for = models.ForeignKey(
        RegisterFor,
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True
    )

    first_name = models.CharField(
        max_length=100
    )

    last_name = models.CharField(
        max_length=100,
        blank=True
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        null=True,
        blank=True
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    email = models.EmailField(
        unique=True,
        blank=True,
        null=True
    )

    phone = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True
    )

    google_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True
    )

    auth_provider = models.CharField(
        max_length=20,
        choices=AUTH_PROVIDER_CHOICES,
        default="PHONE",
        null=True,
        blank=True
    )

    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "users"

    def __str__(self):
        return f"{self.first_name} ({self.phone})"
    

# otp models
class OTP(BaseModel):

    phone = models.CharField(max_length=15)

    otp = models.CharField(max_length=6)

    is_verified = models.BooleanField(default=False)

    expires_at = models.DateTimeField()

    class Meta:
        db_table = "otps"

    def __str__(self):
        return self.phone