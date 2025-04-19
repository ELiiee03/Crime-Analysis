from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from .models import CrimeData


class CrimeDataForm(forms.ModelForm):
    """Form for editing Crime Data."""
    # Explicitly define the city field to ensure it's properly handled
    city = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter city name'
        }),
        help_text="City where the crime occurred"
    )

    barangay = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter barangay name'
        }),
        help_text="Barangay where the crime occurred"
    )

    offense = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter offense type'
        }),
        help_text="Type of crime committed"
    )

    class Meta:
        model = CrimeData
        fields = ['city', 'barangay', 'date_committed', 'time_committed', 'offense', 'latitude', 'longitude',
                  'severity']
        widgets = {
            'date_committed': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time_committed': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.000001',
                'placeholder': 'Enter latitude (e.g. 14.5995)'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.000001',
                'placeholder': 'Enter longitude (e.g. 120.9842)'
            }),
            'severity': forms.Select(
                attrs={'class': 'form-control'},
                choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')]
            )
        }

    def clean(self):
        """Custom validation to ensure all required fields are properly cleaned"""
        cleaned_data = super().clean()
        
        # Validate city
        city = cleaned_data.get('city')
        if not city or not city.strip():
            self.add_error('city', 'City is required')
        
        # Validate barangay
        barangay = cleaned_data.get('barangay')
        if not barangay or not barangay.strip():
            self.add_error('barangay', 'Barangay is required')
        
        # Validate offense
        offense = cleaned_data.get('offense')
        if not offense or not offense.strip():
            self.add_error('offense', 'Offense is required')
        
        # Validate date
        date_committed = cleaned_data.get('date_committed')
        if not date_committed:
            self.add_error('date_committed', 'Date is required')
        
        # Validate severity
        severity = cleaned_data.get('severity')
        if not severity or severity not in ['High', 'Medium', 'Low']:
            self.add_error('severity', 'Select a valid severity level')
            
        return cleaned_data

    def save(self, commit=True):
        """Override save method to ensure city is properly saved"""
        instance = super().save(commit=False)
        
        # Explicitly set fields that might be problematic
        instance.city = self.cleaned_data.get('city', '').strip()
        instance.barangay = self.cleaned_data.get('barangay', '').strip()
        instance.offense = self.cleaned_data.get('offense', '').strip()
        
        if commit:
            instance.save()
        return instance


class CSVUploadForm(forms.Form):
    """Form for uploading CSV files."""
    file = forms.FileField(label='Select a CSV file')


class LoginForm(forms.Form):
    """Form for user login."""
    username = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your password'
    }), required=True)


class CustomUserCreationForm(UserCreationForm):
    """Form for creating a new user."""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter user email'
    }))
    first_name = forms.CharField(required=True, max_length=30, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter first name'
    }))
    last_name = forms.CharField(required=True, max_length=30, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter last name'
    }))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        }


class CustomUserEditForm(UserChangeForm):
    """Form for editing an existing user."""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter user email'
    }))
    first_name = forms.CharField(required=True, max_length=30, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter first name'
    }))
    last_name = forms.CharField(required=True, max_length=30, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter last name'
    }))
    password = forms.CharField(widget=forms.HiddenInput(),
                               required=False)  # Hidden field for password (default behavior in UserChangeForm)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom form for changing the password with additional styling."""
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your current password'
        }),
        label="Current Password",
        required=True,
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        }),
        label="New Password",
        required=True,
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        }),
        label="Confirm New Password",
        required=True,
    )
