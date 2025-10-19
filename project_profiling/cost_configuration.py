"""
Cost Configuration System
Allows dynamic configuration of cost estimation parameters
"""

from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator


class CostConfiguration(models.Model):
    """
    Configuration for cost estimation parameters
    """
    
    PROJECT_TYPES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
        ('infrastructure', 'Infrastructure'),
        ('renovation', 'Renovation'),
    ]
    
    COMPLEXITY_LEVELS = [
        ('low_end', 'Low End (Basic)'),
        ('mid_range', 'Mid Range (Standard)'),
        ('high_end', 'High End (Premium)'),
    ]
    
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPES)
    complexity_level = models.CharField(max_length=10, choices=COMPLEXITY_LEVELS)
    base_cost_per_sqm = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Base cost per square meter in PHP"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['project_type', 'complexity_level']
        ordering = ['project_type', 'complexity_level']
    
    def __str__(self):
        return f"{self.get_project_type_display()} - {self.get_complexity_level_display()} (₱{self.base_cost_per_sqm:,.2f}/sqm)"


class SizeMultiplier(models.Model):
    """
    Configuration for size-based cost multipliers
    """
    
    name = models.CharField(max_length=50, help_text="e.g., Small, Medium, Large")
    min_size = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Minimum lot size in square meters"
    )
    max_size = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True, 
        blank=True,
        help_text="Maximum lot size in square meters (leave blank for no limit)"
    )
    multiplier = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.1')), MaxValueValidator(Decimal('5.0'))],
        help_text="Cost multiplier (e.g., 1.3 = 30% increase, 0.8 = 20% decrease)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['min_size']
    
    def __str__(self):
        max_display = f" - {self.max_size}" if self.max_size else "+"
        return f"{self.name} ({self.min_size}{max_display} sqm): {self.multiplier}x"


class LocationMultiplier(models.Model):
    """
    Configuration for location-based cost multipliers
    """
    
    name = models.CharField(max_length=100, help_text="e.g., Metro Manila, Cebu, Davao")
    keywords = models.TextField(
        help_text="Comma-separated keywords to match in location field (e.g., Manila, Makati, Quezon City)"
    )
    multiplier = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.1')), MaxValueValidator(Decimal('5.0'))],
        help_text="Cost multiplier for this location"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Use this multiplier when no other location matches"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return f"{self.name}: {self.multiplier}x"
    
    def get_keywords_list(self):
        """Get list of keywords for matching"""
        return [keyword.strip().lower() for keyword in self.keywords.split(',') if keyword.strip()]


class ComplexityMultiplier(models.Model):
    """
    Configuration for project category-based complexity multipliers
    """
    
    PROJECT_CATEGORIES = [
        ('PUB', 'Public'),
        ('PRI', 'Private'),
        ('REN', 'Renovation'),
        ('NEW', 'New Build'),
    ]
    
    project_category = models.CharField(max_length=3, choices=PROJECT_CATEGORIES, unique=True)
    multiplier = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.1')), MaxValueValidator(Decimal('5.0'))],
        help_text="Cost multiplier for this project category"
    )
    description = models.TextField(blank=True, help_text="Explanation of why this multiplier is used")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['project_category']
    
    def __str__(self):
        return f"{self.get_project_category_display()}: {self.multiplier}x"


class CostBreakdownTemplate(models.Model):
    """
    Templates for cost breakdown percentages by project type
    """
    
    project_type = models.CharField(max_length=20, choices=CostConfiguration.PROJECT_TYPES)
    complexity_level = models.CharField(max_length=10, choices=CostConfiguration.COMPLEXITY_LEVELS)
    
    # Cost category percentages (should add up to 100%)
    materials_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=40.00)
    labor_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=30.00)
    equipment_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    permits_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    contingency_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    overhead_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['project_type', 'complexity_level']
        ordering = ['project_type', 'complexity_level']
    
    def __str__(self):
        return f"{self.get_project_type_display()} - {self.get_complexity_level_display()} Breakdown"
    
    def clean(self):
        """Validate that percentages add up to 100%"""
        from django.core.exceptions import ValidationError
        
        total = (
            self.materials_percentage + 
            self.labor_percentage + 
            self.equipment_percentage + 
            self.permits_percentage + 
            self.contingency_percentage + 
            self.overhead_percentage
        )
        
        if abs(total - 100) > 0.01:  # Allow small rounding differences
            raise ValidationError(f"Cost breakdown percentages must add up to 100%. Current total: {total}%")
    
    def get_breakdown_dict(self):
        """Get breakdown as dictionary"""
        return {
            'materials': self.materials_percentage / 100,
            'labor': self.labor_percentage / 100,
            'equipment': self.equipment_percentage / 100,
            'permits': self.permits_percentage / 100,
            'contingency': self.contingency_percentage / 100,
            'overhead': self.overhead_percentage / 100,
        }
