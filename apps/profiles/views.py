from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
import csv
from django.http import HttpResponse
from .models import Profile
from apps.accounts.models import User
from .forms import ProfileForm, UserForm, PartnerPreferenceForm
from django.db.models import Q
from django.db.models.functions import Concat , Lower
from django.db.models import Q, Value
# ---------- LISTING ----------
# Only real registered members show up here - staff/admin accounts are excluded.
@staff_member_required
def user_dashboard(request):
    users = User.objects.filter(
        is_staff=False,
        is_superuser=False
    ).select_related('role', 'register_for', 'profile', 'partner_preference').order_by('-id')

    return render(request, 'profiles/user_dashboard.html', {
        'users': users,
        'total_users': users.count(),
    })


# ---------- CREATE (User + Profile together, one page) ----------
@staff_member_required
def create_user(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = ProfileForm(request.POST, request.FILES)
        preference_form = PartnerPreferenceForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid() and preference_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            preference = preference_form.save(commit=False)
            preference.user = user
            preference.created_by = request.user
            preference.save()
            messages.success(request, 'User created successfully with partner preferences.')
            return redirect('user-dashboard')
    else:
        user_form = UserForm()
        profile_form = ProfileForm()
        preference_form = PartnerPreferenceForm(initial={
            'minimum_age': 18,
            'maximum_age': 60,
            'minimum_height': 4.00,
            'maximum_height': 7.00,
        })

    return render(request, 'profiles/user_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'preference_form': preference_form,
    })


# ---------- EDIT (User + Profile together, one page) ----------
@staff_member_required
def edit_user(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    profile = getattr(user_obj, 'profile', None)  # None if no profile filled in yet
    preference = getattr(user_obj, 'partner_preference', None)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user_obj)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        preference_form = PartnerPreferenceForm(request.POST, instance=preference)

        if user_form.is_valid() and profile_form.is_valid() and preference_form.is_valid():
            user_form.save()
            
            new_profile = profile_form.save(commit=False)
            new_profile.user = user_obj
            new_profile.save()
            
            new_pref = preference_form.save(commit=False)
            new_pref.user = user_obj
            if not preference:
                new_pref.created_by = request.user
            new_pref.updated_by = request.user
            new_pref.save()
            
            messages.success(request, 'User updated successfully with partner preferences.')
            return redirect('user-dashboard')
    else:
        user_form = UserForm(instance=user_obj)
        profile_form = ProfileForm(instance=profile)
        preference_form = PartnerPreferenceForm(instance=preference)

    return render(request, 'profiles/user_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'preference_form': preference_form,
        'user_obj': user_obj,
    })


# ---------- DELETE ----------
@staff_member_required
def delete_user(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user_obj.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('user-dashboard')
    return render(request, 'profiles/user_delete.html', {'user_obj': user_obj})


# ---------- VIEW (read-only, User + Profile together) ----------
@staff_member_required
def user_detail(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    profile = getattr(user_obj, 'profile', None)
    preference = getattr(user_obj, 'partner_preference', None)
    return render(request, 'profiles/user_detail.html', {
        'user_obj': user_obj,
        'profile': profile,
        'preference': preference,
    })


# ---------- EXPORT CSV ----------
@staff_member_required
def export_users_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'First Name', 'Last Name', 'Email', 'Phone', 'Gender', 'DOB', 'Role', 'Registered For', 'Active'])
    
    users = User.objects.filter(is_staff=False, is_superuser=False).select_related('role', 'register_for')
    for u in users:
        writer.writerow([
            u.id,
            u.first_name,
            u.last_name,
            u.email or '',
            u.phone or '',
            u.gender or '',
            u.date_of_birth or '',
            u.role.name if u.role else '',
            u.register_for.name if u.register_for else '',
            'Yes' if u.is_active else 'No'
        ])
        
    return response



# search 

from django.db.models import Q, Value
from django.db.models.functions import Concat, Lower


@staff_member_required
def user_dashboard(request):
    search = request.GET.get('search', '').strip()

    users = User.objects.filter(
        is_staff=False,
        is_superuser=False
    ).select_related('role', 'register_for', 'profile', 'partner_preference').annotate(
        full_name=Concat('first_name', Value(' '), 'last_name')
    ).order_by('-id')

    if search:
        search_lower = search.lower()
        users = users.annotate(
            full_name_lower=Lower('full_name'),
            first_name_lower=Lower('first_name'),
            last_name_lower=Lower('last_name'),
            email_lower=Lower('email'),
        ).filter(
            Q(full_name_lower__icontains=search_lower) |
            Q(first_name_lower__icontains=search_lower) |
            Q(last_name_lower__icontains=search_lower) |
            Q(email_lower__icontains=search_lower) |
            Q(phone__icontains=search)
        )

    return render(request, 'profiles/user_dashboard.html', {
        'users': users,
        'total_users': users.count(),
        'search': search,
    })