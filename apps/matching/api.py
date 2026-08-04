from ninja import Router
from ninja_jwt.authentication import JWTAuth
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.accounts.models import User
from .services import MatchService, InterestService, ShortlistService, IgnoreService, BlockService
from .schemas import (
    MatchResponseSchema,
    InterestSendSchema,
    InterestUpdateSchema,
    InterestResponseSchema,
    ShortlistCreateSchema,
    IgnoreCreateSchema,
    BlockCreateSchema,
    MessageResponseSchema,
)

router = Router(tags=["Matching"])

match_service = MatchService()
interest_service = InterestService()
shortlist_service = ShortlistService()
ignore_service = IgnoreService()
block_service = BlockService()


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def serialize_profile(from_user, target_user):
    profile = getattr(target_user, "profile", None)
    if not profile:
        return None
    # Recalculate match score dynamically
    score, matched_fields = match_service.calculate_match_score(from_user, target_user)
    is_mutual = False
    if hasattr(target_user, "partner_preference") and target_user.partner_preference:
        reverse_score, _ = match_service.calculate_match_score(target_user, from_user)
        if score >= 40 and reverse_score >= 40:
            is_mutual = True

    return MatchResponseSchema(
        user_id=target_user.id,
        first_name=target_user.first_name,
        last_name=target_user.last_name,
        profile_photo=profile.profile_photo.url if profile.profile_photo else None,
        age=match_service.calculate_age(target_user.date_of_birth),
        city=profile.city,
        state=profile.state,
        country=profile.country,
        occupation=profile.occupation,
        education=profile.highest_education,
        religion=profile.religion,
        caste=profile.caste,
        match_percentage=score,
        matched_fields=matched_fields,
        is_mutual=is_mutual,
    )


def serialize_interest(interest, current_user):
    # Display the other user's profile details
    display_user = interest.to_user if interest.from_user == current_user else interest.from_user
    profile = getattr(display_user, "profile", None)
    
    return InterestResponseSchema(
        id=interest.id,
        from_user=interest.from_user.id,
        to_user=interest.to_user.id,
        first_name=display_user.first_name,
        last_name=display_user.last_name,
        profile_photo=profile.profile_photo.url if (profile and profile.profile_photo) else None,
        age=match_service.calculate_age(display_user.date_of_birth) if display_user.date_of_birth else None,
        city=profile.city if profile else None,
        state=profile.state if profile else None,
        country=profile.country if profile else None,
        occupation=profile.occupation if profile else None,
        education=profile.highest_education if profile else None,
        religion=profile.religion if profile else None,
        caste=profile.caste if profile else None,
        message=interest.message,
        status=interest.status,
        is_seen=interest.is_seen,
        created_at=interest.created_at,
    )


# ---------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------

@router.get(
    "/recommendations",
    auth=JWTAuth(),
    response=list[MatchResponseSchema]
)
def get_recommendations(request):
    user = request.user
    matches = match_service.get_recommendations(user)
    
    response = []
    for match in matches:
        profile = match.to_user.profile
        response.append(
            MatchResponseSchema(
                user_id=match.to_user.id,
                first_name=match.to_user.first_name,
                last_name=match.to_user.last_name,
                profile_photo=profile.profile_photo.url if profile.profile_photo else None,
                age=match_service.calculate_age(match.to_user.date_of_birth),
                city=profile.city,
                state=profile.state,
                country=profile.country,
                occupation=profile.occupation,
                education=profile.highest_education,
                religion=profile.religion,
                caste=profile.caste,
                match_percentage=match.match_percentage,
                matched_fields=match.matched_fields,
                is_mutual=match.is_mutual,
            )
        )
    return response


# ---------------------------------------------------------------------
# Interest APIs
# ---------------------------------------------------------------------

@router.post(
    "/interest/send",
    auth=JWTAuth(),
    response={200: InterestResponseSchema, 400: MessageResponseSchema}
)
def send_interest(request, payload: InterestSendSchema):
    to_user = get_object_or_404(User, id=payload.to_user)
    try:
        interest = interest_service.send_interest(request.user, to_user, payload.message)
        return 200, serialize_interest(interest, request.user)
    except ValidationError as e:
        return 400, MessageResponseSchema(success=False, message=str(e.message))


@router.get(
    "/interest/sent",
    auth=JWTAuth(),
    response=list[InterestResponseSchema]
)
def get_sent_interests(request):
    interests = interest_service.get_sent_interests(request.user)
    return [serialize_interest(i, request.user) for i in interests]


@router.get(
    "/interest/received",
    auth=JWTAuth(),
    response=list[InterestResponseSchema]
)
def get_received_interests(request):
    interests = interest_service.get_received_interests(request.user)
    return [serialize_interest(i, request.user) for i in interests]


@router.put(
    "/interest/{interest_id}/update",
    auth=JWTAuth(),
    response={200: InterestResponseSchema, 400: MessageResponseSchema}
)
def update_interest(request, interest_id: int, payload: InterestUpdateSchema):
    status_upper = payload.status.upper()
    try:
        if status_upper == "ACCEPTED":
            interest = interest_service.accept_interest(interest_id, request.user)
        elif status_upper == "REJECTED":
            interest = interest_service.reject_interest(interest_id, request.user)
        elif status_upper == "WITHDRAWN":
            interest = interest_service.withdraw_interest(interest_id, request.user)
        else:
            return 400, MessageResponseSchema(success=False, message="Invalid interest status action.")
        return 200, serialize_interest(interest, request.user)
    except ValidationError as e:
        return 400, MessageResponseSchema(success=False, message=str(e.message))


@router.delete(
    "/interest/{interest_id}",
    auth=JWTAuth(),
    response={200: MessageResponseSchema, 400: MessageResponseSchema}
)
def delete_interest(request, interest_id: int):
    try:
        interest_service.delete_interest(interest_id, request.user)
        return 200, MessageResponseSchema(success=True, message="Interest record deleted successfully.")
    except ValidationError as e:
        return 400, MessageResponseSchema(success=False, message=str(e.message))


# ---------------------------------------------------------------------
# Shortlist APIs
# ---------------------------------------------------------------------

@router.post(
    "/shortlist/add",
    auth=JWTAuth(),
    response={200: MessageResponseSchema, 400: MessageResponseSchema}
)
def add_to_shortlist(request, payload: ShortlistCreateSchema):
    shortlisted_user = get_object_or_404(User, id=payload.user)
    try:
        shortlist_service.add_to_shortlist(request.user, shortlisted_user)
        return 200, MessageResponseSchema(success=True, message="Profile shortlisted successfully.")
    except ValidationError as e:
        return 400, MessageResponseSchema(success=False, message=str(e.message))


@router.get(
    "/shortlist",
    auth=JWTAuth(),
    response=list[MatchResponseSchema]
)
def get_shortlisted_profiles(request):
    shortlists = shortlist_service.get_shortlisted_profiles(request.user)
    profiles = []
    for s in shortlists:
        serialized = serialize_profile(request.user, s.shortlisted_user)
        if serialized:
            profiles.append(serialized)
    return profiles


@router.delete(
    "/shortlist/remove/{user_id}",
    auth=JWTAuth(),
    response={200: MessageResponseSchema, 400: MessageResponseSchema}
)
def remove_from_shortlist(request, user_id: int):
    shortlisted_user = get_object_or_404(User, id=user_id)
    try:
        shortlist_service.remove_from_shortlist(request.user, shortlisted_user)
        return 200, MessageResponseSchema(success=True, message="Profile removed from shortlist.")
    except ValidationError as e:
        return 400, MessageResponseSchema(success=False, message=str(e.message))


# ---------------------------------------------------------------------
# Ignore APIs
# ---------------------------------------------------------------------

@router.post(
    "/ignore/add",
    auth=JWTAuth(),
    response={200: MessageResponseSchema, 400: MessageResponseSchema}
)
def ignore_profile(request, payload: IgnoreCreateSchema):
    to_user = get_object_or_404(User, id=payload.user)
    try:
        ignore_service.ignore_profile(request.user, to_user)
        return 200, MessageResponseSchema(success=True, message="Profile ignored successfully.")
    except ValidationError as e:
        return 400, MessageResponseSchema(success=False, message=str(e.message))


@router.get(
    "/ignore",
    auth=JWTAuth(),
    response=list[MatchResponseSchema]
)
def get_ignored_profiles(request):
    ignores = ignore_service.get_ignored_profiles(request.user)
    profiles = []
    for i in ignores:
        serialized = serialize_profile(request.user, i.to_user)
        if serialized:
            profiles.append(serialized)
    return profiles


@router.delete(
    "/ignore/remove/{user_id}",
    auth=JWTAuth(),
    response={200: MessageResponseSchema, 400: MessageResponseSchema}
)
def remove_ignored_profile(request, user_id: int):
    to_user = get_object_or_404(User, id=user_id)
    try:
        ignore_service.remove_ignored_profile(request.user, to_user)
        return 200, MessageResponseSchema(success=True, message="Profile removed from ignored list.")
    except ValidationError as e:
        return 400, MessageResponseSchema(success=False, message=str(e.message))


# ---------------------------------------------------------------------
# Block APIs
# ---------------------------------------------------------------------

@router.post(
    "/block/add",
    auth=JWTAuth(),
    response={200: MessageResponseSchema, 400: MessageResponseSchema}
)
def block_profile(request, payload: BlockCreateSchema):
    to_user = get_object_or_404(User, id=payload.user)
    try:
        block_service.block_profile(request.user, to_user)
        return 200, MessageResponseSchema(success=True, message="Profile blocked successfully.")
    except ValidationError as e:
        return 400, MessageResponseSchema(success=False, message=str(e.message))


@router.get(
    "/block",
    auth=JWTAuth(),
    response=list[MatchResponseSchema]
)
def get_blocked_profiles(request):
    blocks = block_service.get_blocked_profiles(request.user)
    profiles = []
    for b in blocks:
        serialized = serialize_profile(request.user, b.to_user)
        if serialized:
            profiles.append(serialized)
    return profiles


@router.delete(
    "/block/remove/{user_id}",
    auth=JWTAuth(),
    response={200: MessageResponseSchema, 400: MessageResponseSchema}
)
def unblock_profile(request, user_id: int):
    to_user = get_object_or_404(User, id=user_id)
    try:
        block_service.unblock_profile(request.user, to_user)
        return 200, MessageResponseSchema(success=True, message="Profile unblocked successfully.")
    except ValidationError as e:
        return 400, MessageResponseSchema(success=False, message=str(e.message))