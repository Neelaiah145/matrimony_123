from decimal import Decimal
from typing import Optional

from ninja import Schema


class PartnerPreferenceCreateSchema(Schema):
    minimum_age: int
    maximum_age: int

    minimum_height: Decimal
    maximum_height: Decimal

    religion: Optional[str] = None
    caste: Optional[str] = None

    education: Optional[str] = None
    profession: Optional[str] = None

    minimum_salary: Optional[Decimal] = None
    maximum_salary: Optional[Decimal] = None

    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None

    diet: Optional[str] = None
    smoking: Optional[str] = None
    drinking: Optional[str] = None
    horoscope_preferences: Optional[str] = None


class PartnerPreferenceUpdateSchema(Schema):
    minimum_age: Optional[int] = None
    maximum_age: Optional[int] = None

    minimum_height: Optional[Decimal] = None
    maximum_height: Optional[Decimal] = None

    religion: Optional[str] = None
    caste: Optional[str] = None

    education: Optional[str] = None
    profession: Optional[str] = None

    minimum_salary: Optional[Decimal] = None
    maximum_salary: Optional[Decimal] = None

    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None

    diet: Optional[str] = None
    smoking: Optional[str] = None
    drinking: Optional[str] = None
    horoscope_preferences: Optional[str] = None


class PartnerPreferenceResponseSchema(Schema):
    id: int

    minimum_age: int
    maximum_age: int

    minimum_height: Decimal
    maximum_height: Decimal

    religion: str
    caste: str

    education: str
    profession: str

    minimum_salary: Optional[Decimal]
    maximum_salary: Optional[Decimal]

    country: str
    state: str
    city: str

    diet: str
    smoking: str
    drinking: str
    horoscope_preferences: str