from django.shortcuts import get_object_or_404

from .models import PartnerPreference


def create_partner_preference(user, payload):
    """
    Create partner preference for logged-in user.
    """

    if PartnerPreference.objects.filter(user=user, is_active=True).exists():
        raise ValueError("Partner preference already exists.")

    preference = PartnerPreference.objects.create(
        user=user,
        created_by=user,
        **payload.dict()
    )

    return preference


def get_partner_preference(user):
    """
    Get logged-in user's partner preference.
    """

    return get_object_or_404(
        PartnerPreference,
        user=user,
        is_active=True
    )


def update_partner_preference(user, payload):
    """
    Update partner preference.
    """

    preference = get_object_or_404(
        PartnerPreference,
        user=user,
        is_active=True
    )

    data = payload.dict(exclude_unset=True)

    for field, value in data.items():
        setattr(preference, field, value)

    preference.updated_by = user
    preference.save()

    return preference


def delete_partner_preference(user):
    """
    Soft delete partner preference.
    """

    preference = get_object_or_404(
        PartnerPreference,
        user=user,
        is_active=True
    )

    preference.is_active = False
    preference.updated_by = user
    preference.save()

    return {
        "message": "Partner preference deleted successfully."
    }