from django.db import models
from django.conf import settings


class Profile(models.Model):

    MARITAL_STATUS_CHOICES = [
        ("Never Married", "Never Married"),
        ("Divorced", "Divorced"),
        ("Widowed", "Widowed"),
    ]

    DIET_CHOICES = [
        ("Vegetarian", "Vegetarian"),
        ("Non-Vegetarian", "Non-Vegetarian"),
        ("Eggetarian", "Eggetarian"),
    ]

    YES_NO_CHOICES = [
        ("Yes", "Yes"),
        ("No", "No"),
        ("Occasionally", "Occasionally"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )

    # Profile Media
    profile_photo = models.ImageField(
        upload_to="profile_photos/", blank=True, null=True
    )

    video_introduction = models.FileField(
        upload_to="profile_videos/", blank=True, null=True
    )

    # About
    about_me = models.TextField(blank=True)

    # Physical Attributes
    height = models.DecimalField(max_digits=4, decimal_places=2)
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    complexion = models.CharField(max_length=100, blank=True)

    # Education
    highest_education = models.CharField(max_length=255)

    # Employment
    occupation = models.CharField(max_length=255)

    annual_income = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True
    )

    # Religion
    religion = models.CharField(max_length=100)

    caste = models.CharField(max_length=100, blank=True)

    # Horoscope
    rashi = models.CharField(max_length=100, blank=True)

    nakshatra = models.CharField(max_length=100, blank=True)

    dosha = models.CharField(max_length=100, blank=True)

    # Family
    family_information = models.TextField(blank=True)

    # Lifestyle
    diet = models.CharField(max_length=20, choices=DIET_CHOICES)

    smoking = models.CharField(max_length=20, choices=YES_NO_CHOICES)

    drinking = models.CharField(max_length=20, choices=YES_NO_CHOICES)

    # Languages & Hobbies
    languages_known = models.CharField(
        max_length=255, help_text="Example: Telugu, English, Hindi"
    )

    hobbies_interests = models.TextField(blank=True)

    # Marital Status
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES)

    # Disability
    disability_information = models.TextField(blank=True)

    # Location
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "profiles"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
