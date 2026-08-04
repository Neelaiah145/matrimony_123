from django.urls import path
from .views import (
    login_view,
    register_view,
    admin_login_view,
    admin_dashboard,
    admin_logout_view,
    admin_forgot_password_view,
    admin_reset_password_view,
)

urlpatterns = [
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),

    path("", admin_login_view, name="admin-login"),

    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),

    path("admin-logout/", admin_logout_view, name="admin-logout"),
    path("admin-forgot-password/", admin_forgot_password_view, name="admin-forgot-password"),
    path("admin-reset-password/<str:uidb64>/<str:token>/", admin_reset_password_view, name="admin-reset-password"),
    # path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]


