from ninja import ModelSchema, Schema
from .models import Profile


class ProfileOut(ModelSchema):
    class Meta:
        model = Profile
        fields = [
            "id", "profile_photo", "video_introduction", "about_me",
            "height", "weight", "complexion", "highest_education",
            "occupation", "annual_income", "religion", "caste",
            "rashi", "nakshatra", "dosha", "family_information",
            "diet", "smoking", "drinking", "languages_known",
            "hobbies_interests", "marital_status",
            "disability_information", "country", "state", "city", "created_at", "updated_at",
        ]


class ProfileIn(Schema):
    about_me: str = ""
    height: float
    weight: float | None = None
    complexion: str = ""
    highest_education: str
    occupation: str
    annual_income: float | None = None
    religion: str
    caste: str = ""
    rashi: str = ""
    nakshatra: str = ""
    dosha: str = ""
    family_information: str = ""
    diet: str
    smoking: str
    drinking: str
    languages_known: str
    hobbies_interests: str = ""
    marital_status: str
    disability_information: str = ""
    country: str = ""
    state: str = ""
    city: str = ""


class ProfileUpdate(Schema):
    about_me: str | None = None
    height: float | None = None
    weight: float | None = None
    complexion: str | None = None
    highest_education: str | None = None
    occupation: str | None = None
    annual_income: float | None = None
    religion: str | None = None
    caste: str | None = None
    rashi: str | None = None
    nakshatra: str | None = None
    dosha: str | None = None
    family_information: str | None = None
    diet: str | None = None
    smoking: str | None = None
    drinking: str | None = None
    languages_known: str | None = None
    hobbies_interests: str | None = None
    marital_status: str | None = None
    disability_information: str | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None