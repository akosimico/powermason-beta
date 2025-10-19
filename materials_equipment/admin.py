from django.contrib import admin
from .models import (
    Material, MaterialPriceMonitoring, Equipment, Manpower,
    GeneralRequirement, ProjectMaterial, ProjectEquipment,
    ProjectManpower, ProjectGeneralRequirement
)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['name', 'unit', 'standard_price', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['category', 'name']


@admin.register(MaterialPriceMonitoring)
class MaterialPriceMonitoringAdmin(admin.ModelAdmin):
    list_display = ['material', 'supplier_type', 'supplier_name', 'price', 'date', 'is_active']
    list_filter = ['supplier_type', 'is_active', 'date']
    search_fields = ['material__name', 'supplier_name']
    date_hierarchy = 'date'
    ordering = ['-date']


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'ownership_type', 'rental_rate', 'purchase_price', 'is_active']
    list_filter = ['ownership_type', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(Manpower)
class ManpowerAdmin(admin.ModelAdmin):
    list_display = ['role', 'daily_rate', 'is_active']
    list_filter = ['is_active']
    search_fields = ['role']
    ordering = ['role']


@admin.register(GeneralRequirement)
class GeneralRequirementAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'unit_cost', 'unit', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['category', 'name']


@admin.register(ProjectMaterial)
class ProjectMaterialAdmin(admin.ModelAdmin):
    list_display = ['project', 'material', 'quantity', 'unit_price', 'supplier_type', 'total_cost']
    list_filter = ['supplier_type', 'purchase_date']
    search_fields = ['project__project_name', 'material__name']
    date_hierarchy = 'purchase_date'
    ordering = ['-created_at']


@admin.register(ProjectEquipment)
class ProjectEquipmentAdmin(admin.ModelAdmin):
    list_display = ['project', 'equipment', 'start_date', 'end_date', 'daily_rate', 'quantity']
    list_filter = ['start_date', 'end_date']
    search_fields = ['project__project_name', 'equipment__name']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']


@admin.register(ProjectManpower)
class ProjectManpowerAdmin(admin.ModelAdmin):
    list_display = ['project', 'manpower', 'quantity', 'daily_rate', 'start_date', 'end_date']
    list_filter = ['start_date', 'end_date']
    search_fields = ['project__project_name', 'manpower__role']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']


@admin.register(ProjectGeneralRequirement)
class ProjectGeneralRequirementAdmin(admin.ModelAdmin):
    list_display = ['project', 'requirement', 'quantity', 'unit_cost', 'total_cost']
    list_filter = ['purchase_date']
    search_fields = ['project__project_name', 'requirement__name']
    date_hierarchy = 'purchase_date'
    ordering = ['-created_at']
