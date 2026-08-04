from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import Permission
from apps.accounts.models import Role
from django.db.models import Q
from collections import OrderedDict

def role_permissions_view(request):

    roles = Role.objects.prefetch_related("permissions").all()

    if request.method == "POST":

        # Remove all permissions first
        for role in roles:
            role.permissions.clear()

        # Assign selected permissions
        for item in request.POST.getlist("permissions"):

            role_id, permission_id = item.split("_")

            role = Role.objects.get(id=role_id)

            role.permissions.add(permission_id)

        messages.success(request, "Permissions updated successfully.")

        return redirect("role_permissions")

    # Group permissions by app name
    modules = OrderedDict()

    permissions = Permission.objects.select_related(
        "content_type"
    ).order_by(
        "content_type__app_label",
        "name"
    )

    for permission in permissions:

        module = permission.content_type.app_label.title()

        modules.setdefault(module, []).append(permission)

    # Used by template:
    # {% if permission.id in role.permission_ids %}
    for role in roles:

        role.permission_ids = list(
            role.permissions.values_list("id", flat=True)
        )

    context = {
        "roles": roles,
        "modules": modules,
    }

    return render(
        request,
        "permissions.html",
        context,
    )

def role_permissions(request):
    search = request.GET.get("search", "")

    roles = Role.objects.prefetch_related(
        "permissions",
        "users"
    ).all()

    if search:
        roles = roles.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search)
        )

    context = {
        "roles": roles,
        "search": search,
    }

    return render(
        request,
        "roles/role_list.html",
        context,
    )


def role_create(request):

    permissions = Permission.objects.select_related(
        "content_type"
    ).order_by(
        "content_type__app_label",
        "name",
    )

    if request.method == "POST":

        name = request.POST.get("name")
        code = request.POST.get("code")
        description = request.POST.get("description")
        permission_ids = request.POST.getlist("permissions")

        if Role.objects.filter(name=name).exists():
            messages.error(request, "Role with this name already exists.")
            return redirect("role_create")

        if Role.objects.filter(code=code).exists():
            messages.error(request, "Role with this code already exists.")
            return redirect("role_create")

        role = Role.objects.create(
            name=name,
            code=code,
            description=description,
        )

        role.permissions.set(permission_ids)

        messages.success(request, "Role created successfully.")

        return redirect("roles")

    return render(
        request,
        "roles/role_create.html",
        {
            "permissions": permissions,
            "title": "Create Role",
        },
    )

def role_detail(request, pk):

    role = get_object_or_404(
        Role.objects.prefetch_related(
            "permissions",
            "users",
        ),
        pk=pk,
    )

    return render(
        request,
        "roles/role_detail.html",
        {
            "role": role,
        },
    )

def role_edit(request, pk):

    role = get_object_or_404(Role, pk=pk)

    permissions = Permission.objects.select_related(
        "content_type"
    ).order_by(
        "content_type__app_label",
        "name",
    )

    if request.method == "POST":

        name = request.POST.get("name")
        code = request.POST.get("code")
        description = request.POST.get("description")

        if Role.objects.filter(name=name).exclude(pk=pk).exists():
            messages.error(request, "Role with this name already exists.")
            return redirect("role_edit", pk=pk)

        if Role.objects.filter(code=code).exclude(pk=pk).exists():
            messages.error(request, "Role with this code already exists.")
            return redirect("role_edit", pk=pk)

        role.name = name
        role.code = code
        role.description = description
        role.save()

        permission_ids = request.POST.getlist("permissions")

        role.permissions.set(permission_ids)

        messages.success(request, "Role updated successfully.")

        return redirect("roles")

    context = {
        "role": role,
        "permissions": permissions,
        "title": "Edit Role",
    }

    return render(
        request,
        "roles/role_edit.html",
        context,
    )

def role_delete(request, pk):

    role = get_object_or_404(Role, pk=pk)

    if role.users.exists():

        messages.error(
            request,
            "This role is assigned to users and cannot be deleted.",
        )

        return redirect("roles")

    role.delete()

    messages.success(request, "Role deleted successfully.")

    return redirect("roles")