from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import login as django_login, logout as django_logout
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.contrib import messages
from apps.accounts.models import User

def admin_dashboard(request):
    return render(request, 'admin-dashboard.html')
# User Login and Register Page Views
def login_view(request):
    return render(request, "accounts/login.html", {
        "google_client_id": settings.GOOGLE_CLIENT_ID
    })

def register_view(request):
    return render(request, "accounts/register.html", {
        "google_client_id": settings.GOOGLE_CLIENT_ID
    })


# Admin Authentication Views
def admin_login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        if not email or not password:
            messages.error(request, "Please enter email and password.")
            return render(request, "accounts/admin_login.html")

        user = User.objects.filter(email=email).first()

        if not user:
            messages.error(request, "Email is not registered.")
            return render(request, "accounts/admin_login.html")

        if not check_password(password, user.password):
            messages.error(request, "Incorrect password for this email.")
            return render(request, "accounts/admin_login.html")

        if user.role.code not in ["ADMIN", "SUPER_ADMIN"]:
            messages.error(request, "Access denied: You are not authorized as an admin.")
            return render(request, "accounts/admin_login.html")

        if not user.is_active:
            messages.error(request, "Your account is disabled.")
            return render(request, "accounts/admin_login.html")

        # Log user in
        django_login(request, user)
        
        # Display message on current page and set redirect timer on frontend
        messages.success(request, "Signed in successfully! Redirecting...")
        return render(request, "accounts/admin_login.html", {
            "redirect_url": "/admin-dashboard/",
            "redirect_delay": 2000
        })

    return render(request, "accounts/admin_login.html")


def admin_logout_view(request):
    django_logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("admin-login")


def admin_forgot_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if not email:
            messages.error(request, "Please enter your email.")
            return render(request, "accounts/admin_forgot_password.html")

        user = User.objects.filter(email=email).first()
        if not user or user.role.code not in ["ADMIN", "SUPER_ADMIN"]:
            messages.error(request, "This email is not registered as an admin.")
            return render(request, "accounts/admin_forgot_password.html")

        # Generate reset link
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = request.build_absolute_uri(f"/admin-reset-password/{uid}/{token}/")

        # Send mail (printed to console in development)
        subject = "Matrimony Admin Password Reset Link"
        message = f"Hello {user.first_name},\n\nPlease click the link below to reset your password:\n\n{reset_url}\n\nThank you!"
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

        messages.success(request, "Password reset link sent to your email! Redirecting...")
        return render(request, "accounts/admin_forgot_password.html", {
            "redirect_url": "/",
            "redirect_delay": 2000
        })

    return render(request, "accounts/admin_forgot_password.html")


def admin_reset_password_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            password = request.POST.get("password", "")
            confirm_password = request.POST.get("confirm_password", "")

            if not password or len(password) < 8:
                messages.error(request, "Password must be at least 8 characters long.")
                return render(request, "accounts/admin_reset_password.html")

            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return render(request, "accounts/admin_reset_password.html")

            # Update password
            user.password = make_password(password)
            user.save()

            messages.success(request, "Password reset successfully! Redirecting...")
            return render(request, "accounts/admin_reset_password.html", {
                "redirect_url": "/",
                "redirect_delay": 2000
            })

        return render(request, "accounts/admin_reset_password.html")
    else:
        messages.error(request, "This password reset link is invalid or has expired.")
        return render(request, "accounts/admin_reset_password.html", {"invalid_link": True})


def admin_dashboard(request):
    if not request.user.is_authenticated or request.user.role.code not in ["ADMIN", "SUPER_ADMIN"]:
        messages.error(request, "Please log in to access the administrator dashboard.")
        return redirect("admin-login")
        
    from apps.accounts.models import User, Role
    from apps.profiles.models import Profile
    from apps.preferences.models import PartnerPreference
    
    context = {
        'total_users': User.objects.filter(is_staff=False, is_superuser=False).count(),
        'total_roles': Role.objects.count(),
        'total_profiles': Profile.objects.count(),
        'total_preferences': PartnerPreference.objects.filter(is_active=True).count(),
    }
    return render(request, 'admin-dashboard.html', context)

