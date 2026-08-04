from ninja import Router
from ninja.errors import HttpError

from ninja_jwt.authentication import JWTAuth

from .schemas import (
    PartnerPreferenceCreateSchema,
    PartnerPreferenceUpdateSchema,
    PartnerPreferenceResponseSchema,
)

from .services import (
    create_partner_preference,
    get_partner_preference,
    update_partner_preference,
    delete_partner_preference,
)

router = Router(tags=["Partner Preferences"])


@router.post("/",auth=JWTAuth(),response=PartnerPreferenceResponseSchema)
def create_preference(request, payload: PartnerPreferenceCreateSchema):
    """
    Create Partner Preference
    """

    try:
        return create_partner_preference(
            request.user,
            payload
        )

    except ValueError as e:
        raise HttpError(400, str(e))


@router.get("/",auth=JWTAuth(),response=PartnerPreferenceResponseSchema)
def get_preference(request):
    """
    Get Logged-in User Preference
    """

    return get_partner_preference(request.user)


@router.put("/",auth=JWTAuth(),response=PartnerPreferenceResponseSchema)
def update_preference(
    request,
    payload: PartnerPreferenceUpdateSchema
):
    """
    Update Partner Preference
    """

    return update_partner_preference(
        request.user,
        payload
    )


@router.delete("/",auth=JWTAuth())
def delete_preference(request):
    """
    Delete Partner Preference
    """

    return delete_partner_preference(
        request.user
    )