from django.contrib import admin
from .models import (
    ProjectTask, ProgressUpdate, ProgressFile, SystemReport, TaskCost,
    ProjectScope, ScopeBudget, TaskMaterial, TaskEquipment, TaskManpower,
    WeeklyProgressReport, WeeklyReportAttachment
)

@admin.register(ProjectTask)
class ProjectTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "task_name", "project", "scope", "start_date", "end_date", "get_progress")
    search_fields = ("task_name", "project__project_name", "scope__name")
    list_filter = ("project", "scope", "assigned_to", "status")
    readonly_fields = ("duration_days", "manhours")

    def get_progress(self, obj):
        # Get latest approved update
        latest_update = obj.updates.filter(status="A").order_by("-created_at").first()
        return f"{latest_update.progress_percent}%" if latest_update else "No updates"
    
    get_progress.short_description = "Progress"

@admin.register(ProjectScope)
class ProjectScopeAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'weight', 'is_deleted', 'has_tasks')
    list_filter = ('project', 'is_deleted')
    search_fields = ('name', 'project__project_name')
    readonly_fields = ('has_tasks',)

    def has_tasks(self, obj):
        """Display if the scope has tasks"""
        return obj.has_tasks
    has_tasks.boolean = True
    has_tasks.short_description = "Has Tasks?"

@admin.register(ScopeBudget)
class ScopeBudgetAdmin(admin.ModelAdmin):
    list_display = ('scope', 'project', 'allocated_amount', 'allocated_to_tasks', 'remaining_budget', 'utilization_percentage')
    list_filter = ('project',)
    search_fields = ('scope__name', 'project__project_name')
    readonly_fields = ('allocated_to_tasks', 'remaining_budget', 'utilization_percentage')
    
    def utilization_percentage(self, obj):
        return f"{obj.utilization_percentage:.1f}%"
    utilization_percentage.short_description = "Utilization %"

@admin.register(TaskCost)
class TaskCostAdmin(admin.ModelAdmin):
    list_display = ("task", "cost", "allocated_amount")
    search_fields = ("task__task_name", "cost__name")
    list_filter = ("task__project", "task__scope")

@admin.register(TaskMaterial)
class TaskMaterialAdmin(admin.ModelAdmin):
    list_display = ("task", "material", "quantity_needed", "unit_cost", "total_cost")
    list_filter = ("task__project", "material")
    search_fields = ("task__task_name", "material__name")

@admin.register(TaskEquipment)
class TaskEquipmentAdmin(admin.ModelAdmin):
    list_display = ("task", "equipment", "allocation_type", "quantity", "days_needed", "total_cost")
    list_filter = ("task__project", "allocation_type", "equipment")
    search_fields = ("task__task_name", "equipment__name")

@admin.register(TaskManpower)
class TaskManpowerAdmin(admin.ModelAdmin):
    list_display = ("task", "labor_type", "description", "number_of_workers", "days_needed", "total_cost")
    list_filter = ("task__project", "labor_type")
    search_fields = ("task__task_name", "description")

@admin.register(WeeklyProgressReport)
class WeeklyProgressReportAdmin(admin.ModelAdmin):
    list_display = ("report_number", "project", "week_start_date", "week_end_date", "status", "submitted_by", "submitted_at")
    list_filter = ("status", "project", "week_start_date")
    search_fields = ("project__project_name", "report_number")
    readonly_fields = ("report_number", "submitted_at", "reviewed_at")

@admin.register(WeeklyReportAttachment)
class WeeklyReportAttachmentAdmin(admin.ModelAdmin):
    list_display = ("weekly_report", "filename", "file_size", "uploaded_at")
    list_filter = ("uploaded_at", "weekly_report__project")
    search_fields = ("filename", "weekly_report__project__project_name")