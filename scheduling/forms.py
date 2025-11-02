from django import forms
from django.forms import inlineformset_factory
from .models import (
    ProjectTask, ProgressUpdate, ProgressFile, ProjectScope,
    TaskMaterial, TaskEquipment, TaskManpower, ProjectSchedule
)
from authentication.models import UserProfile
from materials_equipment.models import Material, Equipment, ProjectManpower
from datetime import timedelta

class ProjectTaskForm(forms.ModelForm):
    class Meta:
        model = ProjectTask
        fields = ["scope", "task_name", "assigned_to", "start_date", "end_date", "duration_days", "manhours", "weight"]

        labels = {
            "scope": "Project Scope",
            "task_name": "Task Name",
            "assigned_to": "Assign To",
            "start_date": "Start Date",
            "end_date": "End Date",
            "duration_days": "Duration (Days)",
            "manhours": "Man Hours",
            "weight": "Task Weight (%)",
        }
        
        widgets = {
            "task_name": forms.TextInput(attrs={
                "placeholder": "Enter task name...",
                "class": "w-full",
                "id": "id_task_name"
            }),
            "start_date": forms.DateInput(attrs={
                "type": "date", 
                "id": "id_start_date",
                "class": "w-full"
            }),
            "end_date": forms.DateInput(attrs={
                "type": "date", 
                "id": "id_end_date",
                "class": "w-full"
            }),
            "duration_days": forms.NumberInput(attrs={
                "readonly": "readonly",
                "class": "w-full bg-gray-50 cursor-not-allowed",
                "id": "id_duration_days",
                "placeholder": "Auto-calculated"
            }),
            "manhours": forms.NumberInput(attrs={
                "class": "w-full",
                "id": "id_manhours",
                "placeholder": "Enter total manhours required",
                "step": "0.01",
                "min": "0"
            }),
            "weight": forms.NumberInput(attrs={
                "placeholder": "0.00",
                "step": "0.01",
                "min": "0",
                "max": "100",
                "class": "w-full",
                "id": "id_weight"
            }),
        }

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        # Scope field - limit to current project's scopes
        if self.project:
            self.fields["scope"].queryset = ProjectScope.objects.filter(project=self.project)
            self.fields["scope"].empty_label = "Select a scope"
            self.fields["scope"].widget.attrs.update({
                "class": "w-full",
                "id": "id_scope"
            })
        
        # Assigned To field - only show Project Managers
        self.fields["assigned_to"].queryset = UserProfile.objects.filter(role="PM")
        self.fields["assigned_to"].required = False
        self.fields["assigned_to"].widget = forms.HiddenInput()  # We'll use custom JS widget
        
        # Add help text
        self.fields["weight"].help_text = "Percentage contribution of this task to its scope (0-100%)"
        self.fields["duration_days"].help_text = "Automatically calculated from start and end dates"
        self.fields["manhours"].help_text = "Total manhours required for this task"
        self.fields["manhours"].required = True  # Make it required

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")
        weight = cleaned_data.get("weight")
        scope = cleaned_data.get("scope")

        # Validate dates
        if start and end:
            if end < start:
                self.add_error("end_date", "End date cannot be earlier than start date.")
            else:
                # Auto-calculate days (inclusive)
                duration = (end - start).days + 1
                cleaned_data["duration_days"] = duration
                # Remove auto-calculation for manhours - user must enter manually

        # Validate weight within scope
        if weight is not None and scope:
            if weight <= 0:
                self.add_error("weight", "Weight must be greater than 0.")
        elif weight > 100:
            self.add_error("weight", "Weight cannot exceed 100%.")
        else:
            # Check if total weight for scope would exceed 100%
            existing_tasks = ProjectTask.objects.filter(scope=scope).exclude(
                id=self.instance.id if self.instance else None
            )
            current_total = sum(task.weight for task in existing_tasks)

            if current_total + weight > 100:
                remaining = 100 - current_total
                self.add_error(
                    "weight",
                    f"This scope already has {current_total}%. "
                    f"Only {remaining}% remaining, but you entered {weight}%."
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Ensure project is set
        if self.project:
            instance.project = self.project
            
        if commit:
            instance.save()
            
        return instance

class ProgressUpdateForm(forms.ModelForm):
    class Meta:
        model = ProgressUpdate
        fields = ["progress_percent", "remarks"]
        widgets = {
            "progress_percent": forms.NumberInput(attrs={
                "class": "w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500",
                "placeholder": "Enter % progress",
                "step": "0.01",
                "min": "0",
                "max": "100"
            }),
            "remarks": forms.Textarea(attrs={
                "class": "w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500",
                "placeholder": "Additional notes or remarks...",
                "rows": 3
            }),
        }


# ========================================
# RESOURCE ALLOCATION FORMS (Inline with Task)
# ========================================

class TaskMaterialForm(forms.ModelForm):
    class Meta:
        model = TaskMaterial
        fields = ['material', 'quantity_needed', 'unit_cost', 'notes']
        widgets = {
            'material': forms.Select(attrs={'class': 'w-full'}),
            'quantity_needed': forms.NumberInput(attrs={
                'class': 'w-full',
                'placeholder': 'Quantity',
                'step': '0.01',
                'min': '0'
            }),
            'unit_cost': forms.NumberInput(attrs={
                'class': 'w-full',
                'placeholder': 'Unit Cost',
                'step': '0.01',
                'min': '0'
            }),
            'notes': forms.TextInput(attrs={
                'class': 'w-full',
                'placeholder': 'Notes (optional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        # Get all materials from materials_equipment module (not project-specific)
        materials = Material.objects.filter(is_active=True)
        self.fields['material'].queryset = materials
        self.fields['material'].empty_label = "Select material..."

        # Add data attributes to material options for auto-fill
        material_choices = [(m.id, m.name) for m in materials]
        self.fields['material'].widget.choices = [(m.id, m.name) for m in materials]

        # Store material prices as data attributes
        for material in materials:
            option_attrs = {'data-standard-price': float(material.standard_price)}
            self.fields['material'].widget.attrs[f'data-material-{material.id}'] = float(material.standard_price)

        # Pre-fill unit cost with standard price if material is already selected
        if self.instance and self.instance.pk and self.instance.material:
            if not self.instance.unit_cost:
                self.instance.unit_cost = self.instance.material.standard_price


class TaskEquipmentForm(forms.ModelForm):
    class Meta:
        model = TaskEquipment
        fields = ['equipment', 'allocation_type', 'quantity', 'days_needed', 'daily_rate', 'notes']
        widgets = {
            'equipment': forms.Select(attrs={'class': 'w-full'}),
            'allocation_type': forms.Select(attrs={'class': 'w-full'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full',
                'placeholder': 'Quantity',
                'min': '1',
                'value': '1'
            }),
            'days_needed': forms.NumberInput(attrs={
                'class': 'w-full',
                'placeholder': 'Days',
                'min': '1'
            }),
            'daily_rate': forms.NumberInput(attrs={
                'class': 'w-full',
                'placeholder': 'Daily Rate',
                'step': '0.01',
                'min': '0'
            }),
            'notes': forms.TextInput(attrs={
                'class': 'w-full',
                'placeholder': 'Notes (optional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        # Get all equipment from materials_equipment module (not project-specific)
        equipment_list = Equipment.objects.filter(is_active=True)
        self.fields['equipment'].queryset = equipment_list
        self.fields['equipment'].empty_label = "Select equipment..."

        # Store equipment data as widget attributes for auto-fill
        for equip in equipment_list:
            self.fields['equipment'].widget.attrs[f'data-equipment-{equip.id}-type'] = equip.ownership_type
            self.fields['equipment'].widget.attrs[f'data-equipment-{equip.id}-rate'] = float(equip.rental_rate) if equip.rental_rate else 0

        # Pre-fill based on equipment ownership type
        if self.instance and self.instance.pk and self.instance.equipment:
            equip = self.instance.equipment
            if not self.instance.allocation_type:
                self.instance.allocation_type = 'OWNED' if equip.ownership_type == 'OWN' else 'RENTAL'
            if not self.instance.daily_rate and equip.rental_rate:
                self.instance.daily_rate = equip.rental_rate if equip.ownership_type == 'RNT' else 0


class TaskManpowerForm(forms.ModelForm):
    # Add worker dropdown field from ProjectManpower - hidden
    worker = forms.ModelChoiceField(
        queryset=ProjectManpower.objects.none(),
        required=False,
        widget=forms.HiddenInput(),
        label='Select Worker from Project',
        empty_label='Select existing worker...'
    )

    class Meta:
        model = TaskManpower
        fields = ['worker', 'labor_type', 'description', 'number_of_workers', 'daily_rate', 'days_needed', 'notes']
        widgets = {
            'labor_type': forms.Select(attrs={'class': 'w-full'}),
            'description': forms.TextInput(attrs={
                'class': 'w-full',
                'placeholder': 'e.g., Carpenter, Mason, Electrician'
            }),
            'number_of_workers': forms.NumberInput(attrs={
                'class': 'w-full',
                'placeholder': 'Number',
                'min': '1',
                'value': '1'
            }),
            'daily_rate': forms.NumberInput(attrs={
                'class': 'w-full',
                'placeholder': 'Daily Rate',
                'step': '0.01',
                'min': '0'
            }),
            'days_needed': forms.NumberInput(attrs={
                'class': 'w-full',
                'placeholder': 'Days',
                'min': '1'
            }),
            'notes': forms.TextInput(attrs={
                'class': 'w-full',
                'placeholder': 'Notes (optional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        if project:
            # Filter workers by project
            self.fields['worker'].queryset = ProjectManpower.objects.filter(project=project)


# Create formsets for inline editing with 1 extra form (use + button to add more)
TaskMaterialFormSet = inlineformset_factory(
    ProjectTask,
    TaskMaterial,
    form=TaskMaterialForm,
    extra=1,  # Show 1 empty form, use + button to add more
    can_delete=True
)

TaskEquipmentFormSet = inlineformset_factory(
    ProjectTask,
    TaskEquipment,
    form=TaskEquipmentForm,
    extra=1,
    can_delete=True
)

TaskManpowerFormSet = inlineformset_factory(
    ProjectTask,
    TaskManpower,
    form=TaskManpowerForm,
    extra=1,
    can_delete=True
)


# ========================================
# PROJECT SCHEDULE FORMS
# ========================================

class ProjectScheduleForm(forms.ModelForm):
    """Form for uploading project schedule Excel files"""

    class Meta:
        model = ProjectSchedule
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none',
                'accept': '.xlsx,.xls',
                'id': 'schedule_file_input'
            })
        }

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        self.fields['file'].label = 'Upload Schedule File'
        self.fields['file'].help_text = 'Upload Excel file (.xlsx or .xls) - Maximum 10MB'

    def clean_file(self):
        file = self.cleaned_data.get('file')

        if not file:
            raise forms.ValidationError('Please select a file to upload.')

        # Check file extension
        file_name = file.name.lower()
        if not (file_name.endswith('.xlsx') or file_name.endswith('.xls')):
            raise forms.ValidationError('Only Excel files (.xlsx, .xls) are allowed.')

        # Check file size (10MB max)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            raise forms.ValidationError(f'File size must not exceed 10MB. Your file is {file.size / (1024*1024):.2f}MB.')

        return file

    def clean(self):
        cleaned_data = super().clean()

        # Check if project has reached upload limit (5 attempts)
        # Only count non-rejected schedules (rejected schedules don't count towards limit)
        if self.project:
            non_rejected_count = ProjectSchedule.objects.filter(
                project=self.project
            ).exclude(status='REJECTED').count()

            if non_rejected_count >= 5:
                raise forms.ValidationError(
                    'Maximum upload limit reached (5 attempts). Please contact OM or EG for assistance.'
                )

            # Check if an approved schedule already exists
            approved_schedule = ProjectSchedule.objects.filter(
                project=self.project,
                status='APPROVED'
            ).first()

            if approved_schedule:
                raise forms.ValidationError(
                    'This project already has an approved schedule. Cannot upload new schedules.'
                )

        return cleaned_data


class ScheduleRejectionForm(forms.Form):
    """Form for rejecting a schedule with reason"""

    rejection_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full rounded-lg border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500',
            'placeholder': 'Please provide a detailed reason for rejection...',
            'rows': 4,
            'required': True
        }),
        label='Rejection Reason',
        help_text='This will be sent to the Project Manager who uploaded the schedule',
        min_length=10,
        max_length=500
    )