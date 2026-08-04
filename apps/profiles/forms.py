from django import forms
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()


class ProfileForm(forms.ModelForm):
    """
    Used for BOTH creating and editing a profile.
    'user' is intentionally excluded - it's always set explicitly in the view,
    never chosen from a dropdown, so a profile can never be reassigned to the
    wrong account by accident.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add placeholders dynamically to text/number/textarea fields and make them required
        for name, field in self.fields.items():
            widget = field.widget
            if not isinstance(widget, (forms.Select, forms.CheckboxInput, forms.NullBooleanSelect, forms.SelectMultiple)):
                label = field.label or name.replace('_', ' ').capitalize()
                widget.attrs.setdefault('placeholder', f'Enter {label}')
            field.required = True

    class Meta:
        model = Profile
        exclude = ['user']
        widgets = {
            'profile_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'video_introduction': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'about_me': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'height': forms.NumberInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control'}),
            'complexion': forms.TextInput(attrs={'class': 'form-control'}),
            'highest_education': forms.TextInput(attrs={'class': 'form-control'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'annual_income': forms.NumberInput(attrs={'class': 'form-control'}),
            'religion': forms.TextInput(attrs={'class': 'form-control'}),
            'caste': forms.TextInput(attrs={'class': 'form-control'}),
            'rashi': forms.TextInput(attrs={'class': 'form-control'}),
            'nakshatra': forms.TextInput(attrs={'class': 'form-control'}),
            'dosha': forms.TextInput(attrs={'class': 'form-control'}),
            'family_information': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'diet': forms.Select(attrs={'class': 'form-select'}),
            'smoking': forms.Select(attrs={'class': 'form-select'}),
            'drinking': forms.Select(attrs={'class': 'form-select'}),
            'languages_known': forms.TextInput(attrs={'class': 'form-control'}),
            'hobbies_interests': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'marital_status': forms.Select(attrs={'class': 'form-select'}),
            'disability_information': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
        }


class UserForm(forms.ModelForm):
    """
    Used for BOTH creating and editing a User (account details).
    Password is optional: leave blank when editing an existing user
    (so it doesn't get wiped out), fill it in only when admin wants to
    set/change it directly.
    """
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Leave blank to keep unchanged (or if user logs in via OTP)."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.first_name:
                self.fields['first_name'].disabled = True
                self.fields['first_name'].required = False
            if self.instance.last_name:
                self.fields['last_name'].disabled = True
                self.fields['last_name'].required = False
            if self.instance.email:
                self.fields['email'].disabled = True
                self.fields['email'].required = False
            if self.instance.phone:
                self.fields['phone'].disabled = True
                self.fields['phone'].required = False
            if self.instance.gender:
                self.fields['gender'].disabled = True
                self.fields['gender'].required = False
            if self.instance.date_of_birth:
                self.fields['date_of_birth'].disabled = True
                self.fields['date_of_birth'].required = False
        
        # Add placeholders dynamically to text/number/textarea fields and make non-disabled fields required
        for name, field in self.fields.items():
            widget = field.widget
            if not isinstance(widget, (forms.Select, forms.CheckboxInput, forms.NullBooleanSelect, forms.SelectMultiple)):
                label = field.label or name.replace('_', ' ').capitalize()
                widget.attrs.setdefault('placeholder', f'Enter {label}')
            if name != 'password' and not field.disabled:
                field.required = True

    class Meta:
        model = User
        fields = [
            'role', 'register_for', 'first_name', 'last_name',
            'gender', 'date_of_birth', 'email', 'phone',
            'auth_provider', 'is_phone_verified', 'is_email_verified',
            'is_active',
        ]
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'register_for': forms.Select(attrs={'class': 'form-select'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'auth_provider': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_date_of_birth(self):
        from datetime import date
        dob = self.cleaned_data.get('date_of_birth')
        if not dob:
            return None
        age = (date.today() - dob).days // 365
        if age < 18:
            raise forms.ValidationError("User must be at least 18 years old.")
        return dob

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get('password')
        if pwd:
            user.set_password(pwd)
        if commit:
            user.save()
        return user


from apps.preferences.models import PartnerPreference

class PartnerPreferenceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add placeholders dynamically to text/number/textarea fields and make them required
        for name, field in self.fields.items():
            widget = field.widget
            if not isinstance(widget, (forms.Select, forms.CheckboxInput, forms.NullBooleanSelect, forms.SelectMultiple)):
                label = field.label or name.replace('_', ' ').capitalize()
                widget.attrs.setdefault('placeholder', f'Enter {label}')
            field.required = True

    class Meta:
        model = PartnerPreference
        exclude = ['user', 'is_active', 'created_by', 'updated_by']
        widgets = {
            'minimum_age': forms.NumberInput(attrs={'class': 'form-control', 'min': 18}),
            'maximum_age': forms.NumberInput(attrs={'class': 'form-control', 'min': 18}),
            'minimum_height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'maximum_height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'religion': forms.TextInput(attrs={'class': 'form-control'}),
            'caste': forms.TextInput(attrs={'class': 'form-control'}),
            'education': forms.TextInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'minimum_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'maximum_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'diet': forms.Select(attrs={'class': 'form-select'}),
            'smoking': forms.Select(attrs={'class': 'form-select'}),
            'drinking': forms.Select(attrs={'class': 'form-select'}),
            'horoscope_preferences': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }