from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.user_dashboard, name='user-dashboard'),
    path('users/create/', views.create_user, name='create-user'),
    path('users/export/', views.export_users_csv, name='export-users'),
    path('users/<int:pk>/', views.user_detail, name='user-detail'),
    path('users/<int:pk>/edit/', views.edit_user, name='edit-user'),
    path('users/<int:pk>/delete/', views.delete_user, name='delete-user'),
    path('users/export/', views.export_users_csv, name='export-users'),
]