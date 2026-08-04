from datetime import date
from ninja import Schema
from pydantic import EmailStr, field_validator, model_validator


class RegisterSchema(Schema):

    register_for: str
    first_name: str
    last_name: str | None = None
    gender: str
    date_of_birth: date
    email: EmailStr | None = None
    phone: str
    password: str
    confirm_password: str
    accept_terms: bool

    @field_validator("register_for")
    @classmethod
    def validate_register_for(cls, value):

        value = value.strip().upper()

        allowed = [
            "SELF",
            "SON",
            "DAUGHTER",
            "BROTHER",
            "SISTER",
            "FRIEND",
            "RELATIVE",
        ]

        if value not in allowed:
            raise ValueError(
                "Register For must be one of: SELF, SON, DAUGHTER, BROTHER, SISTER, FRIEND, RELATIVE."
            )

        return value

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value):

        value = value.strip().upper()

        if value not in ["MALE", "FEMALE"]:
            raise ValueError("Gender must be MALE or FEMALE.")

        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):

        value = value.strip()

        if not value.isdigit():
            raise ValueError("Phone number must contain only digits.")

        if len(value) != 10:
            raise ValueError("Phone number must be exactly 10 digits.")

        if value[0] not in ["6", "7", "8", "9"]:
            raise ValueError("Invalid Indian mobile number.")

        return value

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, value):

        value = value.strip()

        if not value:
            raise ValueError("First name is required.")

        return value

    @field_validator("last_name")
    @classmethod
    def validate_last_name(cls, value):

        if value:
            return value.strip()

        return value

    @model_validator(mode="after")
    def validate_registration(self):

        if not self.password or not self.password.strip():
            raise ValueError("Password is required.")

        if len(self.password) < 8:
            raise ValueError("Password must be at least 8 characters long.")

        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")

        if not self.accept_terms:
            raise ValueError("Please accept Terms & Conditions.")

        today = date.today()

        age = (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )

        if age < 18:
            raise ValueError(
                "You must be at least 18 years old to register."
            )

        return self

class SendOTPSchema(Schema):
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        value = value.strip()
        if not value.isdigit():
            raise ValueError("Phone number must contain only digits.")
        if len(value) != 10:
            raise ValueError("Phone number must be exactly 10 digits.")
        if value[0] not in ["6", "7", "8", "9"]:
            raise ValueError("Invalid Indian mobile number.")
        return value


class VerifyOTPSchema(Schema):
    phone: str
    otp: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        value = value.strip()
        if not value.isdigit():
            raise ValueError("Phone number must contain only digits.")
        if len(value) != 10:
            raise ValueError("Phone number must be exactly 10 digits.")
        if value[0] not in ["6", "7", "8", "9"]:
            raise ValueError("Invalid Indian mobile number.")
        return value
    
class LoginSchema(Schema):
    phone_or_email: str
    password: str
    

class GoogleLoginSchema(Schema):
    id_token: str
    action: str = "login"
    gender: str | None = None
    register_for: str | None = None
    date_of_birth: str | None = None
    phone: str | None = None
class GoogleRegisterSchema(Schema):
    first_name: str
    last_name: str | None = None
    email: EmailStr
    google_id: str

class ErrorResponseSchema(Schema):
    success: bool = False
    message: str


class ForgotPasswordSendOTPSchema(Schema):
    phone_or_email: str


class ForgotPasswordVerifyOTPSchema(Schema):
    phone_or_email: str
    otp: str


class ForgotPasswordResetSchema(Schema):
    phone_or_email: str
    password: str
    confirm_password: str
    otp: str

    @model_validator(mode="after")
    def validate_password_reset(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self