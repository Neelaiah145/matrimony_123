from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models

from apps.accounts.models import BaseModel


class PartnerPreference(BaseModel):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="partner_preference"
    )

    # Preferred Age
    minimum_age = models.PositiveIntegerField()
    maximum_age = models.PositiveIntegerField()

    # Height Range
    minimum_height = models.DecimalField(max_digits=4,decimal_places=2)
    maximum_height = models.DecimalField(max_digits=4,decimal_places=2)

    # Religion
    religion = models.CharField(max_length=100,blank=True)

    # Caste
    caste = models.CharField(max_length=100,blank=True)

    # Education
    education = models.CharField(max_length=255,blank=True)

    # Profession
    profession = models.CharField(max_length=255,blank=True)

    # Salary Range
    minimum_salary = models.DecimalField(max_digits=12,decimal_places=2,blank=True,null=True)
    maximum_salary = models.DecimalField(max_digits=12,decimal_places=2,blank=True,null=True)

    # Location
    country = models.CharField(
        max_length=100,
        blank=True
    )

    state = models.CharField(
        max_length=100,
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

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

    diet = models.CharField(max_length=20, choices=DIET_CHOICES, blank=True)
    smoking = models.CharField(max_length=20, choices=YES_NO_CHOICES, blank=True)
    drinking = models.CharField(max_length=20, choices=YES_NO_CHOICES, blank=True)

    # Horoscope Preferences
    horoscope_preferences = models.TextField(
        blank=True
    )

    class Meta:
        db_table = "partner_preferences"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.user.first_name} Partner Preference"