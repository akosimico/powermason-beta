# employees/admin.py
from django.contrib import admin
from .models import Employee, ProjectAssignment


class ProjectAssignmentInline(admin.TabularInline):
    model = ProjectAssignment
    extra = 1
    autocomplete_fields = ['project']
    fields = ['project', 'assigned_date', 'end_date', 'is_lead', 'hourly_rate', 'notes']
    show_change_link = True


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'employee_id', 'full_name', 'role', 'status',
        'department', 'hire_date', 'contract_end_date',
        'days_until_contract_expiry', 'auto_deactivated'
    )
    list_filter = ('role', 'status', 'department', 'contract_end_date')
    search_fields = ('employee_id', 'first_name', 'last_name', 'email', 'phone')
    readonly_fields = ('uuid', 'created_at', 'updated_at', 'auto_deactivated')
    ordering = ('last_name', 'first_name')
    date_hierarchy = 'hire_date'
    inlines = [ProjectAssignmentInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('uuid', 'employee_id', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Employment Details', {
            'fields': ('role', 'status', 'hire_date', 'contract_end_date', 'department', 'labor_count')
        }),
        ('Contract Tracking', {
            'fields': ('contract_expiry_notified', 'auto_deactivated')
        }),
        ('System Access', {
            'fields': ('user_profile',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by')
        }),
    )

    # Custom actions
    actions = ['activate_employees', 'deactivate_employees', 'reset_notifications']

    @admin.action(description="Activate selected employees")
    def activate_employees(self, request, queryset):
        for employee in queryset:
            employee.activate()

    @admin.action(description="Deactivate selected employees")
    def deactivate_employees(self, request, queryset):
        for employee in queryset:
            employee.deactivate(reason='manual')

    @admin.action(description="Reset notification status for selected employees")
    def reset_notifications(self, request, queryset):
        queryset.update(contract_expiry_notified=False)


@admin.register(ProjectAssignment)
class ProjectAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        'employee', 'project', 'assigned_date', 'end_date',
        'is_lead', 'hourly_rate', 'is_active'
    )
    list_filter = ('is_lead', 'assigned_date', 'end_date')
    search_fields = ('employee__first_name', 'employee__last_name', 'project__name')
    date_hierarchy = 'assigned_date'
    autocomplete_fields = ['employee', 'project']
