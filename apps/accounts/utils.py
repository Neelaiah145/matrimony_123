import random
import re
from datetime import date, timedelta
from django.utils import timezone
from apps.accounts.models import OTP


def generate_otp():
    """
    Generate 6 digit OTP
    """
    return str(random.randint(100000, 999999))


def otp_expiry_time():
    """
    OTP Expiry Time (5 Minutes)
    """
    return timezone.now() + timedelta(minutes=5)


def create_otp(phone):
    """
    Create New OTP
    """

    # Delete old OTP
    OTP.objects.filter(phone=phone).delete()

    otp = generate_otp()

    OTP.objects.create(
        phone=phone,
        otp=otp,
        expires_at=otp_expiry_time()
    )

    return otp


def verify_otp(phone, otp):
    """
    Verify OTP
    """

    try:

        otp_obj = OTP.objects.get(
            phone=phone,
            otp=otp
        )

    except OTP.DoesNotExist:
        return False, "Invalid OTP"

    if otp_obj.expires_at < timezone.now():
        return False, "OTP Expired"

    otp_obj.is_verified = True
    otp_obj.save(update_fields=["is_verified"])

    return True, "OTP Verified"


def resend_otp(phone):
    """
    Resend OTP
    """

    otp = create_otp(phone)

    return otp


def validate_phone(phone):

    pattern = r'^[6-9]\d{9}$'

    return bool(re.match(pattern, phone))


def validate_email(email):

    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

    return bool(re.match(pattern, email))


def calculate_age(dob):

    today = date.today()

    age = today.year - dob.year

    if (today.month, today.day) < (dob.month, dob.day):
        age -= 1

    return age


def validate_password(password):

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain one uppercase letter."

    if not re.search(r"[a-z]", password):
        return False, "Password must contain one lowercase letter."

    if not re.search(r"\d", password):
        return False, "Password must contain one number."

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain one special character."

    return True, "Valid Password"