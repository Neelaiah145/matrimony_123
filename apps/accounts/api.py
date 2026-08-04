from datetime import date
from ninja import Router
from django.db import transaction
from django.conf import settings
from apps.accounts.models import OTP, User,Role, RegisterFor
from apps.accounts.schemas import *
from apps.accounts.utils import validate_phone, create_otp
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from ninja_jwt.tokens import RefreshToken



router = Router(tags=["Authentication"])


@router.post("/send-mobile-otp", response={200: dict, 400: ErrorResponseSchema})
@transaction.atomic
def send_mobile_otp(request, payload: SendOTPSchema):

    phone = payload.phone.strip()


    if not validate_phone(phone):
        return 400, {
            "success": False,
            "message": "Invalid mobile number."
        }

    if User.objects.filter(phone=phone).exists():
        return 400, {
            "success": False,
            "message": "Mobile number already registered. Please login."
        }


    otp = create_otp(phone)

   
    print(f"OTP for {phone}: {otp}")

    return {
        "success": True,
        "message": f"OTP sent successfully! Your OTP is: {otp}"
    }
    



@router.post("/verify-mobile-otp", response={200: dict, 400: ErrorResponseSchema})
@transaction.atomic
def verify_mobile_otp(request, payload: VerifyOTPSchema):

    try:

        otp_obj = OTP.objects.get(
            phone=payload.phone
        )

    except OTP.DoesNotExist:

        return 400, {
            "success": False,
            "message": "OTP not found."
        }

    # Check Expiry

    if otp_obj.expires_at < timezone.now():

        otp_obj.delete()

        return 400, {
            "success": False,
            "message": "OTP Expired."
        }

    # Check OTP

    if otp_obj.otp != payload.otp:

        return 400, {
            "success": False,
            "message": "Invalid OTP."
        }

    otp_obj.is_verified = True
    otp_obj.save()

    return {

        "success": True,

        "message": "OTP Verified Successfully."

    }
    
    
@router.post("/register", response={200: dict, 400: ErrorResponseSchema})
@transaction.atomic
def register(request, payload: RegisterSchema):

    # Check Phone Exists

    if User.objects.filter(phone=payload.phone).exists():

        return 400, {

            "success": False,

            "message": "Phone number already registered. Please login."

        }

    # Check Email Exists

    if payload.email:

        if User.objects.filter(email=payload.email).exists():

            return 400, {

                "success": False,

                "message": "Email already registered. Please login."

            }

    # Check OTP
    try:
        otp = OTP.objects.get(
            phone=payload.phone,
            is_verified=True
        )
    except OTP.DoesNotExist:
        return 400, {
            "success": False,
            "message": "Please verify mobile OTP first."
        }



    # Get Customer Role

    role, _ = Role.objects.get_or_create(
        code="CUSTOMER",
        defaults={"name": "Customer", "description": "Default Customer Role"}
    )

    # Get or create RegisterFor
    register_for_obj, _ = RegisterFor.objects.get_or_create(
        name=payload.register_for.upper()
    )

    # Create User

    user = User.objects.create(

        role=role,

        register_for=register_for_obj,

        first_name=payload.first_name,

        last_name=payload.last_name,

        gender=payload.gender,

        date_of_birth=payload.date_of_birth,

        email=payload.email,

        phone=payload.phone,

        password=make_password(payload.password),

        is_phone_verified=True

    )

    # Delete OTP
    otp.delete()



    # Generate JWT
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token

    # Print tokens to backend terminal
    print("\n--- NEW REGISTRATION TOKENS ---")
    print(f"Access Token: {str(access)}")
    print(f"Refresh Token: {str(refresh)}")
    print("--------------------------------\n")

    return {
        "success": True,
        "message": "Registration Successful.",
        "data": {
            "id": user.id,
            "name": user.first_name,
            "phone": user.phone,
            "email": user.email,
            "access_token": str(access),
            "refresh_token": str(refresh)
        }
    }
    
    



@router.post("/login", response={200: dict, 400: ErrorResponseSchema})
def login(request, payload: LoginSchema):
    identifier = payload.phone_or_email.strip()
    is_email = "@" in identifier

    # Find User by Phone or Email
    user = User.objects.filter(phone=identifier).first()
    if not user:
        user = User.objects.filter(email=identifier).first()

    if not user:
        msg = "Email is not registered." if is_email else "Mobile number is not registered."
        return 400, {
            "success": False,
            "message": msg
        }

    # Check Password
    if not check_password(payload.password, user.password):
        msg = "Incorrect password for this email." if is_email else "Incorrect password for this mobile number."
        return 400, {
            "success": False,
            "message": msg
        }

    # Check Active

    if not user.is_active:

        return 400, {

            "success": False,

            "message": "Account Disabled."

        }

    # Generate JWT
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token

    # Print tokens to backend terminal
    print("\n--- USER LOGIN TOKENS ---")
    print(f"Access Token: {str(access)}")
    print(f"Refresh Token: {str(refresh)}")
    print("--------------------------\n")

    return {
        "success": True,
        "message": "Login Successful.",
        "data": {
            "id": user.id,
            "name": user.first_name,
            "phone": user.phone,
            "email": user.email,
            "role": user.role.code,
            "access_token": str(access),
            "refresh_token": str(refresh)
        }
    }


def log_google_login_error(msg):
    try:
        with open("google_login_errors.log", "a") as f:
            f.write(f"{msg}\n")
        print(f"[GOOGLE_LOGIN_ERROR] {msg}")
    except Exception:
        pass

@router.post("/google-login", response={200: dict, 400: ErrorResponseSchema})
@transaction.atomic
def google_login(request, payload: GoogleLoginSchema):
    token = payload.id_token.strip()

    if token.startswith("mock_"):
        email = f"{token}@example.com"
        first_name = "Mock"
        last_name = "User"
        google_id = token
    else:
        import urllib.request
        import json
        try:
            url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode())
                if "error_description" in data:
                    log_google_login_error(f"Google verification failed: {data['error_description']}")
                    return 400, {"success": False, "message": f"Google verification failed: {data['error_description']}"}

                # Verify Client ID / Audience if set
                aud = data.get("aud")
                if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_ID != "your_google_client_id_here" and aud != settings.GOOGLE_CLIENT_ID:
                    log_google_login_error(f"Google verification failed: Audience claim mismatch. aud: {aud}, client_id: {settings.GOOGLE_CLIENT_ID}")
                    return 400, {"success": False, "message": "Google verification failed: Audience claim mismatch."}

                email = data.get("email")
                first_name = data.get("given_name", "Google")
                last_name = data.get("family_name", "User")
                google_id = data.get("sub")
        except Exception as e:
            import traceback
            log_google_login_error(f"Failed to verify Google token: {str(e)}\n{traceback.format_exc()}")
            return 400, {"success": False, "message": f"Failed to verify Google token: {str(e)}"}

    if not email:
        log_google_login_error("Google account does not have an email.")
        return 400, {"success": False, "message": "Google account does not have an email."}

    user = User.objects.filter(google_id=google_id).first()
    if not user:
        user = User.objects.filter(email=email).first()

    action = payload.action.strip().lower()

    if action == "register":
        if user:
            return {
                "success": True,
                "message": "Google account already registered. Please login.",
                "is_new_user": False,
                "data": {
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "google_id": google_id
                }
            }


        # Create a new user automatically using defaults
        try:
            extra_fields = {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "google_id": google_id,
                "auth_provider": "GOOGLE",
                "is_email_verified": True,
            }
            # If Google token contains gender, use it. Otherwise, use payload gender.
            gender_val = None
            if not token.startswith("mock_"):
                g_gender = data.get("gender")
                if g_gender and isinstance(g_gender, str):
                    g_gender_up = g_gender.strip().upper()
                    if g_gender_up in ["MALE", "FEMALE"]:
                        gender_val = g_gender_up
            
            if not gender_val and payload.gender:
                p_gender = payload.gender.strip().upper()
                if p_gender in ["MALE", "FEMALE"]:
                    gender_val = p_gender

            extra_fields["gender"] = gender_val
            if payload.register_for:
                from apps.accounts.models import RegisterFor
                rf = RegisterFor.objects.filter(name=payload.register_for.upper()).first()
                if rf:
                    extra_fields["register_for"] = rf
            if payload.date_of_birth:
                extra_fields["date_of_birth"] = payload.date_of_birth
            if payload.phone:
                extra_fields["phone"] = payload.phone
                extra_fields["is_phone_verified"] = True
            else:
                extra_fields["is_phone_verified"] = False

            user = User.objects.create_user(**extra_fields)
            # Ensure no usable password is set
            user.set_unusable_password()
            user.save()
        except Exception as e:
            import traceback
            log_google_login_error(f"Failed to register Google account: {str(e)}\n{traceback.format_exc()}")
            return 400, {"success": False, "message": f"Failed to register Google account: {str(e)}"}

        return {
            "success": True,
            "message": "Google Account Registered successfully! Redirecting to login page...",
            "is_new_user": True,
            "data": {
                "id": user.id,
                "name": user.first_name,
                "phone": user.phone,
                "email": user.email
            }
        }

    else:  # login
        if not user:
            log_google_login_error(f"Account is not registered. Please register first. email: {email}")
            return 400, {
                "success": False,
                "message": "Account is not registered. Please register first."
            }

        if not user.google_id:
            user.google_id = google_id
            user.auth_provider = "GOOGLE"
            user.save()

        if not user.is_active:
            log_google_login_error(f"Account Disabled. email: {email}")
            return 400, {"success": False, "message": "Account Disabled."}

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        # Print tokens to backend terminal
        print("\n--- GOOGLE LOGIN TOKENS ---")
        print(f"Access Token: {str(access)}")
        print(f"Refresh Token: {str(refresh)}")
        print("----------------------------\n")

        return {
            "success": True,
            "message": "Google Login Successful.",
            "is_new_user": False,
            "data": {
                "id": user.id,
                "name": user.first_name,
                "phone": user.phone,
                "email": user.email,
                "access_token": str(access),
                "refresh_token": str(refresh)
            }
        }

@router.post("/google-register", response={200: dict, 400: ErrorResponseSchema})
@transaction.atomic
def google_register(request, payload: GoogleRegisterSchema):
    # Check Email Exists
    if User.objects.filter(email=payload.email).exists():
        return 400, {
            "success": False,
            "message": "Email already registered. Please login."
        }

    # Check Google ID Exists
    if User.objects.filter(google_id=payload.google_id).exists():
        return 400, {
            "success": False,
            "message": "Google account already registered. Please login."
        }

    # Get Customer Role
    role, _ = Role.objects.get_or_create(
        code="CUSTOMER",
        defaults={"name": "Customer", "description": "Default Customer Role"}
    )

    # Get or create RegisterFor default
    register_for_obj, _ = RegisterFor.objects.get_or_create(
        name="SELF"
    )

    # Create User
    try:
        user = User.objects.create(
            role=role,
            register_for=register_for_obj,
            first_name=payload.first_name,
            last_name=payload.last_name or "",
            email=payload.email,
            google_id=payload.google_id,
            auth_provider="GOOGLE",
            is_email_verified=True,
            is_phone_verified=True,
            password=make_password(None)
        )
        user.set_unusable_password()
        user.save()
    except Exception as e:
        return 400, {
            "success": False,
            "message": f"Failed to register Google account: {str(e)}"
        }

    # Generate JWT
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token

    return {
        "success": True,
        "message": "Google Registration Successful.",
        "data": {
            "id": user.id,
            "name": user.first_name,
            "phone": user.phone,
            "email": user.email,
            "access_token": str(access),
            "refresh_token": str(refresh)
        }
    }


@router.post("/forgot-password-send-otp", response={200: dict, 400: ErrorResponseSchema})
@transaction.atomic
def forgot_password_send_otp(request, payload: ForgotPasswordSendOTPSchema):
    identifier = payload.phone_or_email.strip()
    is_email = "@" in identifier
    
    if is_email:
        user = User.objects.filter(email=identifier).first()
        if not user:
            return 400, {
                "success": False,
                "message": "User with this email does not exist."
            }
        otp = create_otp(user.phone)
        
        # Send OTP to Email
        subject = "Matrimony Password Reset OTP"
        message = f"Hello {user.first_name},\n\nYour password reset OTP code is: {otp}\n\nThank you!"
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        print(f"PASSWORD RESET EMAIL OTP for {user.email}: {otp}")
        msg = "Password reset OTP sent successfully to your email."
    else:
        user = User.objects.filter(phone=identifier).first()
        if not user:
            return 400, {
                "success": False,
                "message": "User with this phone number does not exist."
            }
        otp = create_otp(user.phone)
        print(f"PASSWORD RESET SMS OTP for {user.phone}: {otp}")
        msg = "Password reset OTP sent successfully to your mobile number. Check Django console!"
        
    return {
        "success": True,
        "message": msg
    }


@router.post("/forgot-password-verify-otp", response={200: dict, 400: ErrorResponseSchema})
@transaction.atomic
def forgot_password_verify_otp(request, payload: ForgotPasswordVerifyOTPSchema):
    identifier = payload.phone_or_email.strip()
    
    user = User.objects.filter(phone=identifier).first()
    if not user:
        user = User.objects.filter(email=identifier).first()
        
    if not user:
        return 400, {
            "success": False,
            "message": "User not found."
        }
        
    try:
        otp_obj = OTP.objects.get(phone=user.phone)
    except OTP.DoesNotExist:
        return 400, {
            "success": False,
            "message": "OTP not found."
        }
        
    if otp_obj.expires_at < timezone.now():
        otp_obj.delete()
        return 400, {
            "success": False,
            "message": "OTP Expired."
        }
        
    if otp_obj.otp != payload.otp:
        return 400, {
            "success": False,
            "message": "Invalid OTP."
        }
        
    otp_obj.is_verified = True
    otp_obj.save()
    
    return {
        "success": True,
        "message": "OTP Verified Successfully."
    }


@router.post("/forgot-password-reset", response={200: dict, 400: ErrorResponseSchema})
@transaction.atomic
def forgot_password_reset(request, payload: ForgotPasswordResetSchema):
    identifier = payload.phone_or_email.strip()
    
    user = User.objects.filter(phone=identifier).first()
    if not user:
        user = User.objects.filter(email=identifier).first()
        
    if not user:
        return 400, {
            "success": False,
            "message": "User not found."
        }
        
    try:
        otp = OTP.objects.get(
            phone=user.phone,
            is_verified=True
        )
    except OTP.DoesNotExist:
        return 400, {
            "success": False,
            "message": "Please verify OTP first."
        }
        
    user.password = make_password(payload.password)
    user.save()
    
    otp.delete()
    
    return {
        "success": True,
        "message": "Password reset successfully."
    }
