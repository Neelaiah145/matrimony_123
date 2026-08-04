# Create your models here.
from django.conf import settings
from django.db import models

from apps.accounts.models import BaseModel

class ProfileMatch(BaseModel):

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recommended_profiles"
    )

    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recommended_to"
    )

    match_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    matched_fields = models.JSONField(
        default=list,
        blank=True
    )

    is_mutual = models.BooleanField(
        default=False
    )

    class Meta:
        db_table = "profile_matches"
        ordering = ["-match_percentage"]
        unique_together = ("from_user", "to_user")

    def __str__(self):
        return f"{self.from_user.first_name} → {self.to_user.first_name} ({self.match_percentage}%)"



class IgnoredProfile(BaseModel):
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ignored_profiles"
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ignored_by"
    )

    class Meta:
        db_table = "profile_ignored"
        unique_together = ("from_user", "to_user")

    def __str__(self):
        return f"{self.from_user.first_name} ignored {self.to_user.first_name}"


class BlockedProfile(BaseModel):
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocked_profiles"
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocked_by"
    )

    class Meta:
        db_table = "profile_blocked"
        unique_together = ("from_user", "to_user")

    def __str__(self):
        return f"{self.from_user.first_name} blocked {self.to_user.first_name}"
    
    



class Interest(BaseModel):
    """
    Stores interests sent between users.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"
        EXPIRED = "EXPIRED", "Expired"

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_interests",
        help_text="User who sent the interest."
    )

    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_interests",
        help_text="User who received the interest."
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    message = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        help_text="Optional message while sending interest."
    )

    is_seen = models.BooleanField(
        default=False,
        help_text="Whether receiver viewed this interest."
    )

    responded_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    rejected_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    withdrawn_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "interests"
        ordering = ["-created_at"]
        unique_together = ("from_user", "to_user")

    def __str__(self):
        return (
            f"{self.from_user.first_name} → "
            f"{self.to_user.first_name} "
            f"({self.status})"
        )
        
class Shortlist(BaseModel):
    """
    Stores profiles shortlisted by a user.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shortlisted_profiles",
        help_text="User who shortlisted the profile."
    )

    shortlisted_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shortlisted_by",
        help_text="Profile that was shortlisted."
    )

    class Meta:
        db_table = "shortlists"
        ordering = ["-created_at"]
        unique_together = ("owner", "shortlisted_user")

    def __str__(self):
        return (
            f"{self.owner.first_name} "
            f"shortlisted "
            f"{self.shortlisted_user.first_name}"
        )
        
        
