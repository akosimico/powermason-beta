from django import forms
from django.db.models import Q
from .models import ProjectProfile, ProjectBudget, ProjectType, ProjectScope, CostCategory
from authentication.models import UserProfile
from manage_client.models import Client
from employees.models import Employee



class ProjectProfileForm(forms.ModelForm):
    class Meta:
        model = ProjectProfile
        fields = [
            "project_manager",
            "project_source",
            "project_id",
            "project_name",
            "project_type",
            "project_category",
            "description",
            "client",
            "location",
            "gps_coordinates",
            "city_province",
            "lot_size",
            "start_date",
            "target_completion_date",
            "actual_completion_date",
            "estimated_cost",
            "expense",
            "payment_terms",
            "site_engineer",
            "contract_agreement",
            "permits_licenses",
            # subcontractors removed - managed via project view
            # Team & Resources
            "project_in_charge",
            "safety_officer",
            "quality_assurance_officer",
            "quality_officer",
            "foreman",
            "number_of_laborers",
            # Note: contract_agreement and permits_licenses removed - use Document Library instead
            "status",
            # BOQ fields
            "boq_items",
            "boq_dependencies",
            "extracted_total_cost",
            "extracted_cost_breakdown",
            "boq_file_processed",
            "project_role",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "target_completion_date": forms.DateInput(attrs={"type": "date"}),
            "actual_completion_date": forms.DateInput(attrs={"type": "date"}),
            "location": forms.Textarea(attrs={"rows": 3, "resize": "vertical"}),
            # BOQ fields - hidden, handled by JavaScript
            "boq_items": forms.HiddenInput(),
            "boq_dependencies": forms.HiddenInput(),
            "extracted_total_cost": forms.HiddenInput(),
            "extracted_cost_breakdown": forms.HiddenInput(),
            "boq_file_processed": forms.HiddenInput(),
            "project_role": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        # Extract pre-selected client ID BEFORE calling super()
        self.pre_selected_client_id = kwargs.pop('pre_selected_client_id', None)
        
        super().__init__(*args, **kwargs)

        # ----------------------------
        # Handle Project Manager field
        # ----------------------------
        self.fields["project_manager"].required = False
        
        # ----------------------------
        # Handle BOQ fields - make them non-required
        # ----------------------------
        boq_fields = ["boq_items", "boq_dependencies", "extracted_total_cost", 
                      "extracted_cost_breakdown", "boq_file_processed", "project_role"]
        for field_name in boq_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False
                
        # Store BOQ data for later processing in clean method
        self._boq_items_data = None
        if 'boq_items' in self.data and self.data['boq_items']:
            try:
                import json
                self._boq_items_data = json.loads(self.data['boq_items'])
                print(f"DEBUG: Form - Parsed BOQ data: {len(self._boq_items_data)} items")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"DEBUG: Form - Error parsing BOQ data: {e}")
                pass
        pm_qs = UserProfile.objects.filter(role="PM")

        if self.instance and self.instance.project_manager:
            pm_qs = pm_qs | UserProfile.objects.filter(id=self.instance.project_manager.id)

        pm_id = self.data.get("project_manager")
        if pm_id and pm_id.isdigit():
            pm_qs = pm_qs | UserProfile.objects.filter(id=int(pm_id))

        self.fields["project_manager"].queryset = pm_qs.distinct()
        self.fields["project_manager"].widget.attrs.update({
            "class": "w-full rounded-lg border border-gray-300 bg-white px-3 py-2 shadow-sm "
                     "focus:border-blue-500 focus:ring-2 focus:ring-blue-500 text-gray-700",
        })

        # ----------------------------
        # Handle pre-selected client logic FIRST
        # ----------------------------
        if self.pre_selected_client_id and not self.instance.pk:
            try:
                client = Client.objects.get(id=self.pre_selected_client_id)
                
                # Remove client field from form since it's handled in template
                if 'client' in self.fields:
                    del self.fields['client']
                
                # Filter project types to only show client's available types
                client_project_types = client.project_types.filter(is_active=True)
                if client_project_types.exists():
                    self.fields["project_type"].queryset = client_project_types
                    
                    # Add styling to indicate filtered options
                    self.fields["project_type"].widget.attrs.update({
                        "class": "w-full rounded-lg border border-blue-300 bg-blue-50 px-3 py-2 shadow-sm "
                                 "focus:border-blue-500 focus:ring-2 focus:ring-blue-500 text-gray-700",
                        "data-filtered-by-client": "true"
                    })
                else:
                    # No project types available for this client
                    self.fields["project_type"].queryset = ProjectType.objects.none()
                    self.fields["project_type"].widget.attrs.update({
                        "class": "w-full rounded-lg border border-red-300 bg-red-50 px-3 py-2 shadow-sm text-gray-700",
                        "disabled": True
                    })
                    
            except Client.DoesNotExist:
                pass
        else:
            # ----------------------------
            # Handle Client field (normal case)
            # ----------------------------
            client_qs = Client.objects.filter(is_active=True)

            # Always allow the current client even if inactive
            if self.instance and self.instance.client:
                client_qs = client_qs | Client.objects.filter(id=self.instance.client.id)

            # Also allow posted client ID (when editing via hidden input)
            client_id = self.data.get("client")
            if client_id and client_id.isdigit():
                client_qs = client_qs | Client.objects.filter(id=int(client_id))

            self.fields["client"].queryset = client_qs.distinct()
            self.fields["client"].widget.attrs.update({
                "class": "w-full rounded-lg border border-gray-300 bg-white px-3 py-2 shadow-sm "
                         "focus:border-blue-500 focus:ring-2 focus:ring-blue-500 text-gray-700",
                "data-autofill-target": "true",
                "onchange": "handleClientChange(this.value)"
            })
            
            # ----------------------------
            # Handle Project Type field (normal case)
            # ----------------------------
            self.fields["project_type"].queryset = ProjectType.objects.filter(is_active=True)
            self.fields["project_type"].widget.attrs.update({
                "class": "w-full rounded-lg border border-gray-300 bg-white px-3 py-2 shadow-sm "
                         "focus:border-blue-500 focus:ring-2 focus:ring-blue-500 text-gray-700"
            })

        # ----------------------------
        # Style payment terms field
        # ----------------------------
        if "payment_terms" in self.fields:
            self.fields["payment_terms"].widget.attrs.update({
                "class": "w-full rounded-lg border border-gray-300 bg-white px-3 py-2 shadow-sm "
                         "focus:border-blue-500 focus:ring-2 focus:ring-blue-500 text-gray-700"
            })

            # Add special styling for auto-filled fields
            if self.pre_selected_client_id:
                self.fields["payment_terms"].widget.attrs.update({
                    "data-auto-fillable": "true"
                })

        # ----------------------------
        # Handle Employee Role Fields
        # ----------------------------
        employee_fields = {
            'project_in_charge': 'PIC',
            'safety_officer': 'SO',
            'quality_assurance_officer': 'QA',
            'quality_officer': 'QO',
            'foreman': 'FM'
        }

        for field_name, role in employee_fields.items():
            if field_name in self.fields:
                # Get employees with the specific role and active status
                employee_qs = Employee.objects.filter(role=role, status='active').order_by('last_name', 'first_name')

                # Always include the current employee if exists (even if inactive)
                if self.instance and hasattr(self.instance, field_name):
                    current_employee = getattr(self.instance, field_name)
                    if current_employee:
                        employee_qs = employee_qs | Employee.objects.filter(id=current_employee.id)

                self.fields[field_name].queryset = employee_qs.distinct()
                self.fields[field_name].widget.attrs.update({
                    "class": "w-full rounded-lg border border-gray-300 bg-white px-3 py-2 shadow-sm "
                             "focus:border-blue-500 focus:ring-2 focus:ring-blue-500 text-gray-700",
                    "data-role": role
                })

                # Set empty label
                self.fields[field_name].empty_label = f"Select {self.fields[field_name].help_text or field_name.replace('_', ' ').title()}"

        # ----------------------------
        # Handle Number of Laborers field
        # ----------------------------
        if 'number_of_laborers' in self.fields:
            self.fields['number_of_laborers'].widget.attrs.update({
                "class": "w-full rounded-lg border border-gray-300 bg-white px-3 py-2 shadow-sm "
                         "focus:border-blue-500 focus:ring-2 focus:ring-blue-500 text-gray-700",
                "min": "0",
                "placeholder": "Enter number of laborers"
            })

    def clean(self):
        cleaned_data = super().clean()
        
        # Handle BOQ items data if it was parsed from JSON
        if hasattr(self, '_boq_items_data') and self._boq_items_data:
            print(f"DEBUG: Form clean - Processing BOQ data: {len(self._boq_items_data)} items")
            cleaned_data['boq_items'] = self._boq_items_data
            
            # Calculate cost breakdown from BOQ items
            if self._boq_items_data:
                total_cost = sum(float(item.get('total_cost', 0)) for item in self._boq_items_data)
                cleaned_data['extracted_total_cost'] = total_cost
                
                cost_breakdown = {
                    'materials': sum(float(item.get('material_cost', 0)) for item in self._boq_items_data),
                    'labor': sum(float(item.get('labor_cost', 0)) for item in self._boq_items_data),
                    'equipment': sum(float(item.get('equipment_cost', 0)) for item in self._boq_items_data),
                    'subcontractor': sum(float(item.get('subcontractor_cost', 0)) for item in self._boq_items_data),
                }
                cleaned_data['extracted_cost_breakdown'] = cost_breakdown
                cleaned_data['boq_file_processed'] = True
                print(f"DEBUG: Form clean - Calculated total cost: {total_cost}")
        
        return cleaned_data

class ProjectBudgetForm(forms.ModelForm):
    class Meta:
        model = ProjectBudget
        fields = ['scope', 'category','category_other', 'planned_amount']
        widgets = {
            'scope': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            }),
            'category': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            }),
            'category_other': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Specify category if Other',
            }),
            'planned_amount': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            })
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        # Limit scope choices to this project's scopes
        if project:
            self.fields['scope'].queryset = ProjectScope.objects.filter(project=project)
        
        # Add labels
        self.fields['scope'].label = 'Project Scope'
        self.fields['category'].label = 'Cost Category'
        self.fields['planned_amount'].label = 'Planned Amount (₱)'
        
        # Add help text
        self.fields['scope'].help_text = 'Select the project scope for this budget item'
        self.fields['category'].help_text = 'Select the cost category within this scope'
        self.fields['planned_amount'].help_text = 'Enter the planned budget amount for this scope/category'
        
        # If editing, disable scope/category to prevent duplicate combinations
        if self.instance.pk:
            self.fields['scope'].disabled = True
            self.fields['category'].disabled = True
            
    def clean(self):
        cleaned_data = super().clean()
        scope = cleaned_data.get('scope')
        category = cleaned_data.get('category')
        
        # Check for duplicate scope-category combination (only for new instances)
        if not self.instance.pk and scope and category:
            if ProjectBudget.objects.filter(scope=scope, category=category).exists():
                raise forms.ValidationError(
                    f"A budget for {scope.name} - {self.get_category_display(category)} already exists."
                )
        
        return cleaned_data
    
    def get_category_display(self, category_code):
        """Helper method to get category display name"""
        for code, name in CostCategory.choices:
            if code == category_code:
                return name
        return category_code
