"""
Forms for Project Type management with cost configuration
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import ProjectType


class ProjectTypeForm(forms.ModelForm):
    """Form for creating and editing project types with cost configuration"""
    
    class Meta:
        model = ProjectType
        fields = [
            'name', 'code', 'description', 'is_active',
            'base_cost_low_end', 'base_cost_mid_range', 'base_cost_high_end',
            'materials_percentage', 'labor_percentage', 'equipment_percentage',
            'permits_percentage', 'contingency_percentage', 'overhead_percentage'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., Residential House, Commercial Office'
            }),
            'code': forms.TextInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., RES, COM, IND',
                'style': 'text-transform: uppercase;'
            }),
            'description': forms.Textarea(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Describe this project type...'
            }),
            'base_cost_low_end': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'base_cost_mid_range': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'base_cost_high_end': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'materials_percentage': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '40.00'
            }),
            'labor_percentage': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '30.00'
            }),
            'equipment_percentage': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '10.00'
            }),
            'permits_percentage': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '5.00'
            }),
            'contingency_percentage': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '10.00'
            }),
            'overhead_percentage': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '5.00'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add help text for cost fields
        self.fields['base_cost_low_end'].help_text = 'Base cost per square meter for low-end projects (PHP)'
        self.fields['base_cost_mid_range'].help_text = 'Base cost per square meter for mid-range projects (PHP)'
        self.fields['base_cost_high_end'].help_text = 'Base cost per square meter for high-end projects (PHP)'
        
        # Add help text for percentage fields
        self.fields['materials_percentage'].help_text = 'Percentage of total cost for materials'
        self.fields['labor_percentage'].help_text = 'Percentage of total cost for labor'
        self.fields['equipment_percentage'].help_text = 'Percentage of total cost for equipment'
        self.fields['permits_percentage'].help_text = 'Percentage of total cost for permits'
        self.fields['contingency_percentage'].help_text = 'Percentage of total cost for contingency'
        self.fields['overhead_percentage'].help_text = 'Percentage of total cost for overhead'
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate that percentages add up to 100%
        percentage_fields = [
            'materials_percentage', 'labor_percentage', 'equipment_percentage',
            'permits_percentage', 'contingency_percentage', 'overhead_percentage'
        ]
        
        total_percentage = sum(
            cleaned_data.get(field, 0) or 0 
            for field in percentage_fields
        )
        
        if abs(total_percentage - 100) > 0.01:  # Allow small rounding differences
            raise ValidationError(
                f"Cost breakdown percentages must add up to 100%. "
                f"Current total: {total_percentage:.2f}%"
            )
        
        # Validate that at least one base cost is provided
        cost_fields = ['base_cost_low_end', 'base_cost_mid_range', 'base_cost_high_end']
        has_cost = any(cleaned_data.get(field) for field in cost_fields)
        
        if not has_cost:
            raise ValidationError(
                "At least one base cost per square meter must be provided for cost estimation."
            )
        
        return cleaned_data
    
    def clean_code(self):
        code = self.cleaned_data.get('code', '').upper().strip()
        if not code:
            # Auto-generate code from name
            name = self.cleaned_data.get('name', '')
            if name:
                code = ''.join([word[0].upper() for word in name.split() if word])[:10]
        return code


class ProjectTypeCostConfigForm(forms.ModelForm):
    """Simplified form for just cost configuration"""
    
    class Meta:
        model = ProjectType
        fields = [
            'base_cost_low_end', 'base_cost_mid_range', 'base_cost_high_end',
            'materials_percentage', 'labor_percentage', 'equipment_percentage',
            'permits_percentage', 'contingency_percentage', 'overhead_percentage'
        ]
        widgets = {
            'base_cost_low_end': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'base_cost_mid_range': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'base_cost_high_end': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'materials_percentage': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '40.00'
            }),
            'labor_percentage': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '30.00'
            }),
            'equipment_percentage': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '10.00'
            }),
            'permits_percentage': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '5.00'
            }),
            'contingency_percentage': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '10.00'
            }),
            'overhead_percentage': forms.NumberInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '5.00'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate that percentages add up to 100%
        percentage_fields = [
            'materials_percentage', 'labor_percentage', 'equipment_percentage',
            'permits_percentage', 'contingency_percentage', 'overhead_percentage'
        ]
        
        total_percentage = sum(
            cleaned_data.get(field, 0) or 0 
            for field in percentage_fields
        )
        
        if abs(total_percentage - 100) > 0.01:  # Allow small rounding differences
            raise ValidationError(
                f"Cost breakdown percentages must add up to 100%. "
                f"Current total: {total_percentage:.2f}%"
            )
        
        return cleaned_data
