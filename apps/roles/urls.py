from django.urls import path
from .views import role_permissions_view,role_permissions,role_create,role_detail,role_edit,role_delete

urlpatterns = [
    path(
        "permissions/",
        role_permissions_view,
        name="role_permissions"
    ),
       path(
        "roles/",
        role_permissions,
        name="roles",
    ),
      path(
        "roles/create/",
        role_create,
        name="role_create",
    ),
      path(
        "roles/<int:pk>/",
        role_detail,
        name="role_detail",
    ),

       path(
        "roles/<int:pk>/edit/",
        role_edit,
        name="role_edit",
    ),

    path(
        "roles/<int:pk>/delete/",
        role_delete,
        name="role_delete",
    ),
]