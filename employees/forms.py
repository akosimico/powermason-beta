# employees/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from .models import Employee

User = get_user_model()


class EmployeeForm(forms.ModelForm):
    """Form for creating and editing employees"""
    
    class Meta:
        model = Employee
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'role', 'status', 'hire_date', 'contract_end_date',
            'department', 'labor_count'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'hire_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'contract_end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter department'
            }),
            'labor_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
        }
        help_texts = {
            'email': 'Required for Project Managers to create user accounts',
            'contract_end_date': 'Leave blank for permanent employees',
            'labor_count': 'Number of workers (mainly for Labor role)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make certain fields required based on role
        self.fields['email'].required = False
        self.fields['contract_end_date'].required = False
        
        # Set default hire date to today
        if not self.instance.pk:
            self.fields['hire_date'].initial = date.today()
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        role = self.cleaned_data.get('role')

        # Email is required for Project Managers
        if role == 'PM' and not email:
            raise ValidationError('Email is required for Project Manager role.')

        # For PM role, check if email is already in use
        if role == 'PM' and email:
            # Validate email format
            if not email or '@' not in email:
                raise ValidationError('Please enter a valid email address.')

            # Check if email already exists in User model (exclude current instance if editing)
            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                # If editing and this user is linked to current employee, allow it
                if self.instance.pk and self.instance.user_profile and self.instance.user_profile.user == existing_user:
                    return email
                raise ValidationError('This email is already associated with an existing user account. Please use a different email.')

            # Check if email is already used by another employee
            existing_employee = Employee.objects.filter(email=email).exclude(pk=self.instance.pk if self.instance.pk else None).first()
            if existing_employee:
                raise ValidationError(f'This email is already used by employee: {existing_employee.full_name} ({existing_employee.employee_id})')

        return email
    
    def clean_hire_date(self):
        hire_date = self.cleaned_data.get('hire_date')
        
        if hire_date and hire_date > date.today():
            raise ValidationError('Hire date cannot be in the future.')
        
        return hire_date
    
    def clean_contract_end_date(self):
        contract_end_date = self.cleaned_data.get('contract_end_date')
        hire_date = self.cleaned_data.get('hire_date')
        
        if contract_end_date:
            if hire_date and contract_end_date <= hire_date:
                raise ValidationError('Contract end date must be after hire date.')
            
            if contract_end_date < date.today():
                raise ValidationError('Contract end date cannot be in the past.')
        
        return contract_end_date
    
    def clean_labor_count(self):
        labor_count = self.cleaned_data.get('labor_count')
        role = self.cleaned_data.get('role')
        
        if role != 'LB' and labor_count != 1:
            # Reset to 1 for non-labor roles
            return 1
        
        if labor_count and labor_count < 1:
            raise ValidationError('Labor count must be at least 1.')
        
        return labor_count


class EmployeeFilterForm(forms.Form):
    """Form for filtering employees in the list view"""
    
    ROLE_CHOICES = [('', 'All Roles')] + Employee.EMPLOYEE_ROLE_CHOICES
    STATUS_CHOICES = [('', 'All Statuses')] + Employee.STATUS_CHOICES
    CONTRACT_STATUS_CHOICES = [
        ('', 'All Contracts'),
        ('expiring', 'Expiring Soon (30 days)'),
        ('expired', 'Expired'),
    ]
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, ID, or email...'
        })
    )
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    contract_status = forms.ChoiceField(
        choices=CONTRACT_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class ContractExtensionForm(forms.Form):
    """Form for extending employee contracts"""
    
    new_end_date = forms.DateField(
        label='New Contract End Date',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def __init__(self, employee=None, *args, **kwargs):
        self.employee = employee
        super().__init__(*args, **kwargs)
        
        # Set minimum date to today
        self.fields['new_end_date'].widget.attrs['min'] = date.today().isoformat()
        
        # Set initial value to 1 year from today or current contract end date
        if employee and employee.contract_end_date:
            initial_date = max(employee.contract_end_date, date.today()) + timedelta(days=365)
        else:
            initial_date = date.today() + timedelta(days=365)
        
        self.fields['new_end_date'].initial = initial_date
    
    def clean_new_end_date(self):
        new_end_date = self.cleaned_data.get('new_end_date')
        
        if new_end_date and new_end_date <= date.today():
            raise ValidationError('New contract end date must be in the future.')
        
        if self.employee and self.employee.contract_end_date:
            if new_end_date <= self.employee.contract_end_date:
                raise ValidationError('New end date must be later than current contract end date.')
        
        return new_end_date


class BulkActionForm(forms.Form):
    """Form for bulk actions on employees"""
    
    ACTION_CHOICES = [
        ('', 'Select Action...'),
        ('activate', 'Activate Selected'),
        ('deactivate', 'Deactivate Selected'),
        ('send_notifications', 'Send Contract Notifications'),
        ('export_csv', 'Export to CSV'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    employee_ids = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    def clean_employee_ids(self):
        employee_ids = self.cleaned_data.get('employee_ids', '')
        
        if not employee_ids:
            raise ValidationError('No employees selected.')
        
        try:
            ids = [int(id.strip()) for id in employee_ids.split(',') if id.strip()]
        except ValueError:
            raise ValidationError('Invalid employee IDs.')
        
        if not ids:
            raise ValidationError('No valid employee IDs provided.')
        
        return ids