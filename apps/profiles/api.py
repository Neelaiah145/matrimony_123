from ninja import Router
from ninja.errors import HttpError
from django.shortcuts import get_object_or_404
from ninja_jwt.authentication import JWTAuth

from .models import Profile
from .schemas import ProfileOut, ProfileIn, ProfileUpdate

router = Router(tags=["Profile"], auth=JWTAuth())


@router.get("/profile/", response=ProfileOut)
def get_profile(request):
    profile = Profile.objects.filter(user=request.auth).first()
    if not profile:
        raise HttpError(404, "Profile not found.")
    return profile


@router.post("/profile/", response={201: ProfileOut})
def create_profile(request, payload: ProfileIn):
    if Profile.objects.filter(user=request.auth).exists():
        raise HttpError(400, "Profile already exists. Use PUT to update.")
    profile = Profile.objects.create(user=request.auth, **payload.dict())
    return 201, profile


@router.put("/profile/", response=ProfileOut)
def update_profile(request, payload: ProfileUpdate):
    profile = get_object_or_404(Profile, user=request.auth)
    for attr, value in payload.dict(exclude_none=True).items():
        setattr(profile, attr, value)
    profile.save()
    return profile