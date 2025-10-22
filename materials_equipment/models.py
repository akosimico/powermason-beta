from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class SupplierType(models.TextChoices):
    REGULAR = "REG", "Regular Supplier"
    RANDOM = "RND", "Random Supplier"
    BOTH = "BTH", "Both"
    BOQ = "BOQ", "BOQ Estimate"
    QUOTATION = "QUO", "Project Quotation"


class Material(models.Model):
    """Materials that can be used in projects"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=50, help_text="e.g., kg, meters, pieces")
    standard_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Standard/reference price"
    )
    category = models.CharField(max_length=100, blank=True, help_text="e.g., Cement, Steel, Wood")
    source = models.CharField(max_length=20, blank=True, help_text="Source of material: BOQ, QUOTATION, MANUAL")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.name

    def get_latest_price(self, supplier_type=None):
        """Get the latest price for this material"""
        query = self.price_monitoring.filter(is_active=True).order_by('-date')
        if supplier_type:
            query = query.filter(supplier_type=supplier_type)
        return query.first()


class MaterialPriceMonitoring(models.Model):
    """Track material prices from different suppliers"""
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='price_monitoring')
    supplier_type = models.CharField(max_length=3, choices=SupplierType.choices)
    supplier_name = models.CharField(max_length=200)
    price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text="Set to False for outdated prices")
    # Project relationship for BOQ/Quotation tracking
    project = models.ForeignKey(
        'project_profiling.ProjectProfile',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='price_records',
        help_text="Project this price record is associated with (for BOQ/Quotation types)"
    )
    recorded_by = models.ForeignKey(
        'authentication.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='price_records'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'supplier_type']
        indexes = [
            models.Index(fields=['material', 'date']),
            models.Index(fields=['supplier_type', 'date']),
        ]

    def __str__(self):
        return f"{self.material.name} - {self.get_supplier_type_display()} - ₱{self.price} ({self.date})"

    def price_difference_from_standard(self):
        """Calculate difference from standard price"""
        return self.price - self.material.standard_price

    def price_difference_percentage(self):
        """Calculate percentage difference from standard"""
        if self.material.standard_price > 0:
            return ((self.price - self.material.standard_price) / self.material.standard_price) * 100
        return 0


class ProjectMaterialExtraction(models.Model):
    """Track material extraction history from BOQ/Quotation files"""
    EXTRACTION_SOURCES = [
        ('BOQ', 'BOQ File'),
        ('QUOTATION', 'Quotation File'),
    ]
    
    project = models.ForeignKey(
        'project_profiling.ProjectProfile',
        on_delete=models.CASCADE,
        related_name='material_extractions'
    )
    source_type = models.CharField(max_length=10, choices=EXTRACTION_SOURCES)
    source_file = models.CharField(max_length=500, help_text="Original file name")
    extraction_date = models.DateTimeField(auto_now_add=True)
    materials_count = models.PositiveIntegerField(default=0)
    equipment_count = models.PositiveIntegerField(default=0)
    mobilization_count = models.PositiveIntegerField(default=0)
    total_extracted_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total value of extracted items"
    )
    extraction_notes = models.TextField(blank=True, null=True)
    extracted_by = models.ForeignKey(
        'authentication.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='extractions'
    )
    
    class Meta:
        ordering = ['-extraction_date']
        indexes = [
            models.Index(fields=['project', 'source_type']),
            models.Index(fields=['extraction_date']),
        ]
    
    def __str__(self):
        return f"{self.project.project_name} - {self.get_source_type_display()} ({self.extraction_date})"


class Equipment(models.Model):
    """Equipment that can be rented or owned"""
    OWNERSHIP_CHOICES = [
        ('OWN', 'Owned'),
        ('RNT', 'Rented'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    ownership_type = models.CharField(max_length=3, choices=OWNERSHIP_CHOICES)
    rental_rate = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Daily rental rate (if rented)"
    )
    depreciation_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annual depreciation rate % (if owned)"
    )
    purchase_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Purchase price (if owned)"
    )
    purchase_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['ownership_type']),
        ]

    def __str__(self):
        return self.name


class Manpower(models.Model):
    """Manpower roles and rates"""
    role = models.CharField(max_length=200, help_text="e.g., Foreman, Laborer, Engineer")
    description = models.TextField(blank=True, null=True)
    daily_rate = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['role']
        verbose_name_plural = 'Manpower'

    def __str__(self):
        return f"{self.role} - ₱{self.daily_rate}/day"


class GeneralRequirement(models.Model):
    """General project requirements"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100, help_text="e.g., Safety, Tools, Consumables")
    unit_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unit = models.CharField(max_length=50, help_text="e.g., set, piece, month")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.name} - ₱{self.unit_cost}/{self.unit}"


class ProjectMaterial(models.Model):
    """Materials assigned to a project"""
    project = models.ForeignKey(
        'project_profiling.ProjectProfile',
        on_delete=models.CASCADE,
        related_name='project_materials'
    )
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Actual price used for this project"
    )
    supplier_type = models.CharField(max_length=3, choices=SupplierType.choices)
    supplier_name = models.CharField(max_length=200)
    purchase_date = models.DateField(null=True, blank=True)
    delivered_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    added_by = models.ForeignKey(
        'authentication.UserProfile',
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'material']),
        ]

    def __str__(self):
        return f"{self.project.project_name} - {self.material.name} ({self.quantity})"

    @property
    def total_cost(self):
        """Calculate total cost for this material"""
        return self.quantity * self.unit_price

    def savings_vs_standard(self):
        """Calculate savings compared to standard price"""
        standard_total = self.quantity * self.material.standard_price
        actual_total = self.total_cost
        return standard_total - actual_total


class ProjectEquipment(models.Model):
    """Equipment assigned to a project"""
    project = models.ForeignKey(
        'project_profiling.ProjectProfile',
        on_delete=models.CASCADE,
        related_name='project_equipment'
    )
    equipment = models.ForeignKey(Equipment, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    daily_rate = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Actual daily rate for this project"
    )
    quantity = models.PositiveIntegerField(default=1, help_text="Number of units")
    notes = models.TextField(blank=True, null=True)
    added_by = models.ForeignKey(
        'authentication.UserProfile',
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['project', 'equipment']),
        ]

    def __str__(self):
        return f"{self.project.project_name} - {self.equipment.name}"

    @property
    def days_used(self):
        """Calculate number of days equipment is/was used"""
        if self.end_date:
            return (self.end_date - self.start_date).days + 1
        return None

    @property
    def total_cost(self):
        """Calculate total cost"""
        days = self.days_used
        if days:
            return self.daily_rate * Decimal(days) * self.quantity
        return None


class ProjectManpower(models.Model):
    """Manpower assigned to a project"""
    project = models.ForeignKey(
        'project_profiling.ProjectProfile',
        on_delete=models.CASCADE,
        related_name='project_manpower'
    )
    manpower = models.ForeignKey(Manpower, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1, help_text="Number of workers")
    daily_rate = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Actual daily rate for this project"
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    added_by = models.ForeignKey(
        'authentication.UserProfile',
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name_plural = 'Project Manpower'
        indexes = [
            models.Index(fields=['project', 'manpower']),
        ]

    def __str__(self):
        return f"{self.project.project_name} - {self.manpower.role} x{self.quantity}"

    @property
    def days_worked(self):
        """Calculate number of days worked"""
        if self.end_date:
            return (self.end_date - self.start_date).days + 1
        return None

    @property
    def total_cost(self):
        """Calculate total cost"""
        days = self.days_worked
        if days:
            return self.daily_rate * Decimal(days) * self.quantity
        return None


class ProjectGeneralRequirement(models.Model):
    """General requirements for a project"""
    project = models.ForeignKey(
        'project_profiling.ProjectProfile',
        on_delete=models.CASCADE,
        related_name='project_general_requirements'
    )
    requirement = models.ForeignKey(GeneralRequirement, on_delete=models.PROTECT)
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unit_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Actual cost for this project"
    )
    purchase_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    added_by = models.ForeignKey(
        'authentication.UserProfile',
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'requirement']),
        ]

    def __str__(self):
        return f"{self.project.project_name} - {self.requirement.name}"

    @property
    def total_cost(self):
        """Calculate total cost"""
        return self.quantity * self.unit_cost
