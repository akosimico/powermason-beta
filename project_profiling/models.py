from django.db import models
from authentication.models import UserProfile
from django.db.models import Sum
from decimal import Decimal
from django.utils import timezone
from manage_client.models import Client
from django.apps import apps
from scheduling.models import ProjectScope

class ProjectType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)  # e.g., 'GC', 'DC', 'RES'
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Cost estimation configuration
    base_cost_low_end = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Base cost per sqm for low-end projects (PHP)"
    )
    base_cost_mid_range = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Base cost per sqm for mid-range projects (PHP)"
    )
    base_cost_high_end = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Base cost per sqm for high-end projects (PHP)"
    )
    
    # Cost breakdown percentages (should add up to 100%)
    materials_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=40.00,
        help_text="Percentage of total cost for materials"
    )
    labor_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=30.00,
        help_text="Percentage of total cost for labor"
    )
    equipment_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.00,
        help_text="Percentage of total cost for equipment"
    )
    permits_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=5.00,
        help_text="Percentage of total cost for permits"
    )
    contingency_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.00,
        help_text="Percentage of total cost for contingency"
    )
    overhead_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=5.00,
        help_text="Percentage of total cost for overhead"
    )
    
    # Cost learning tracking fields
    total_projects_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of projects contributing to cost data"
    )
    last_cost_update = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Timestamp of last cost data update"
    )
    
    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Project Type'
        verbose_name_plural = 'Project Types'
    
    def __str__(self):
        return self.name
    
    def get_usage_count(self):
        return self.projects.count()
    
    def get_base_cost(self, complexity_level='mid_range'):
        """Get base cost for specific complexity level"""
        cost_mapping = {
            'low_end': self.base_cost_low_end,
            'mid_range': self.base_cost_mid_range,
            'high_end': self.base_cost_high_end,
        }
        return cost_mapping.get(complexity_level, self.base_cost_mid_range)
    
    def get_cost_breakdown(self):
        """Get cost breakdown as dictionary"""
        return {
            'materials': self.materials_percentage / 100,
            'labor': self.labor_percentage / 100,
            'equipment': self.equipment_percentage / 100,
            'permits': self.permits_percentage / 100,
            'contingency': self.contingency_percentage / 100,
            'overhead': self.overhead_percentage / 100,
        }
    
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
    
    def has_cost_configuration(self):
        """Check if this project type has cost configuration"""
        return any([
            self.base_cost_low_end,
            self.base_cost_mid_range,
            self.base_cost_high_end
        ])
    
    def has_learned_costs(self):
        """Check if this project type has learned costs from actual projects"""
        return self.total_projects_count > 0
    
    def get_confidence_level(self):
        """Get confidence level based on number of contributing projects"""
        if self.total_projects_count == 0:
            return "No Data"
        elif self.total_projects_count < 3:
            return "Low"
        elif self.total_projects_count < 10:
            return "Medium"
        else:
            return "High"


class ProjectTypeCostHistory(models.Model):
    """
    Track cost data from individual projects to build learning database
    """
    
    SOURCE_CHOICES = [
        ('boq_upload', 'BOQ Upload'),
        ('project_completion', 'Project Completion'),
        ('manual_entry', 'Manual Entry'),
    ]
    
    COMPLEXITY_LEVELS = [
        ('low_end', 'Low End'),
        ('mid_range', 'Mid Range'),
        ('high_end', 'High End'),
    ]
    
    project_type = models.ForeignKey(
        ProjectType, 
        on_delete=models.CASCADE, 
        related_name='cost_history'
    )
    project = models.ForeignKey(
        'ProjectProfile', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='cost_contributions'
    )
    
    # Cost data
    lot_size = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Lot size in square meters"
    )
    total_cost = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        help_text="Total project cost in PHP"
    )
    cost_per_sqm = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Cost per square meter"
    )
    
    # Cost breakdown
    materials_cost = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text="Materials cost"
    )
    labor_cost = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text="Labor cost"
    )
    equipment_cost = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text="Equipment cost"
    )
    permits_cost = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text="Permits and fees cost"
    )
    contingency_cost = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text="Contingency cost"
    )
    overhead_cost = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text="Overhead cost"
    )
    
    # Context for better predictions
    location = models.CharField(
        max_length=200, 
        blank=True,
        help_text="Project location"
    )
    project_category = models.CharField(
        max_length=10, 
        blank=True,
        help_text="Project category (PUB, PRI, REN, NEW)"
    )
    complexity_level = models.CharField(
        max_length=10, 
        choices=COMPLEXITY_LEVELS,
        default='mid_range',
        help_text="Project complexity level"
    )
    
    # Role support
    project_role = models.CharField(
        max_length=20,
        choices=[
            ('general_contractor', 'General Contractor'),
            ('subcontractor', 'Subcontractor')
        ],
        default='general_contractor',
        help_text="Role of the company in this project"
    )
    
    # Metadata
    source = models.CharField(
        max_length=20, 
        choices=SOURCE_CHOICES,
        default='boq_upload',
        help_text="Source of cost data"
    )
    is_approved = models.BooleanField(
        default=False,
        help_text="Whether this cost data is approved for learning"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this data was uploaded"
    )
    approved_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When this data was approved"
    )
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Project Type Cost History'
        verbose_name_plural = 'Project Type Cost Histories'
    
    def __str__(self):
        project_name = self.project.project_name if self.project else "BOQ Upload"
        return f"{self.project_type.name} - {project_name} ({self.total_cost:,.2f} PHP)"
    
    def save(self, *args, **kwargs):
        # Calculate cost per sqm
        if self.lot_size and self.total_cost:
            self.cost_per_sqm = self.total_cost / self.lot_size
        super().save(*args, **kwargs)


class Expense(models.Model):
    EXPENSE_TYPES = [
        ('material', 'Material Purchase'),
        ('labor', 'Labor Payment'),
        ('equipment', 'Equipment Rental'),
        ('service', 'Service/Contractor'),
        ('other', 'Other'),
    ]
    
    project = models.ForeignKey('ProjectProfile', on_delete=models.CASCADE, related_name='expenses')
    budget_category = models.ForeignKey('ProjectBudget', on_delete=models.CASCADE, related_name='expenses')
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPES)
    expense_other = models.CharField(max_length=255, blank=True, null=True, help_text="Specify if expense type is other")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    vendor = models.CharField(max_length=255, blank=True)
    receipt_number = models.CharField(max_length=100, blank=True)
    expense_date = models.DateField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-expense_date', '-created_at']
        
class ProjectProfile(models.Model):
    # ----------------------------
    # Choice Definitions
    # ----------------------------
    PROJECT_SOURCES = [
        ("GC", "General Contractor"),
        ("DC", "Direct Client"),
    ]

    PROJECT_CATEGORIES = [
        ("PUB", "Public"),
        ("PRI", "Private"),
        ("REN", "Renovation"),
        ("NEW", "New Build"),
    ]
    STATUS_CHOICES = [
        ("PD", "Pending"),
        ("DR", "Draft"),
        ("PL", "Planned"),
        ("OG", "Ongoing"),
        ("CP", "Completed"),
        ("CN", "Cancelled"),
    ]

    # ----------------------------
    # 1. User Assignments
    # ----------------------------
    created_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name="projects_created",
    )
    assigned_to = models.ForeignKey(
        UserProfile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects_assigned",
    )
    project_manager = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"role": "PM"},
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects"
    )

    # ----------------------------
    # 2. General Project Information
    # ----------------------------
    project_source = models.CharField(max_length=20, choices=PROJECT_SOURCES)
    project_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    project_name = models.CharField(max_length=200)
    project_type = models.ForeignKey(ProjectType, on_delete=models.SET_NULL, null=True, related_name="projects")
    project_category = models.CharField(max_length=10, choices=PROJECT_CATEGORIES, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # ----------------------------
    # 4. Location & Site Details
    # ----------------------------
    location = models.CharField(max_length=300)
    gps_coordinates = models.CharField(max_length=100, blank=True, null=True)
    city_province = models.CharField(max_length=200, blank=True, null=True)
    lot_size = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Lot size in square meters"
    )

    # ----------------------------
    # 5. Timeline
    # ----------------------------
    start_date = models.DateField(blank=True, null=True)
    target_completion_date = models.DateField(blank=True, null=True)
    actual_completion_date = models.DateField(blank=True, null=True)

    # ----------------------------
    # 6. Financials
    # ----------------------------
    estimated_cost = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    approved_budget = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    expense = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    payment_terms = models.TextField(blank=True, null=True)
    downpayment_paid = models.BooleanField(default=False, help_text="Whether client has paid the downpayment")
    downpayment_evidence = models.FileField(
        upload_to='downpayment_evidence/',
        blank=True,
        null=True,
        help_text="Evidence of downpayment (receipt, bank transfer, etc.)"
    )
    downpayment_date = models.DateTimeField(blank=True, null=True, help_text="Date when downpayment was received")

    # ----------------------------
    # 7. Team & Resources
    # ----------------------------
    site_engineer = models.CharField(max_length=200, blank=True, null=True)
    subcontractors = models.TextField(blank=True, null=True)

    # Employee assignments
    project_in_charge = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects_as_pic',
        limit_choices_to={'role': 'PIC', 'status': 'active'},
        help_text='Project In Charge'
    )
    safety_officer = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects_as_so',
        limit_choices_to={'role': 'SO', 'status': 'active'},
        help_text='Safety Officer'
    )
    quality_assurance_officer = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects_as_qa',
        limit_choices_to={'role': 'QA', 'status': 'active'},
        help_text='Quality Assurance Officer'
    )
    quality_officer = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects_as_qo',
        limit_choices_to={'role': 'QO', 'status': 'active'},
        help_text='Quality Officer'
    )
    foreman = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects_as_foreman',
        limit_choices_to={'role': 'FM', 'status': 'active'},
        help_text='Foreman'
    )
    # Number of laborers
    number_of_laborers = models.PositiveIntegerField(
        default=0,
        help_text='Number of laborers assigned to this project'
    )

    # ----------------------------
    # 8. Documentation
    # ----------------------------
    contract_agreement = models.FileField(upload_to="contracts/", blank=True, null=True)
    permits_licenses = models.FileField(upload_to="permits/", blank=True, null=True)

    # ----------------------------
    # 9. Status & Tracking
    # ----------------------------
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PL")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived = models.BooleanField(default=False)
    progress = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Overall project progress (%)"
    )
    
    is_draft = models.BooleanField(default=False, help_text="True if this is a draft")
    submitted_for_approval = models.BooleanField(default=False, help_text="True if submitted for approval")
    approved_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects_approved",
        limit_choices_to={"role": "EG"}
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ["-created_at", "project_name"]

    # ----------------------------
    # Properties / Business Logic
    # ----------------------------
    def __str__(self):
        return f"{self.project_id or 'NoCode'} - {self.project_name}"
    
    def active(self):
        return not self.archived

    @property
    def total_expenses(self):
        return sum(cost.amount for cost in self.costs.all())

    @property
    def cost_performance(self):
        """Return % of budget spent"""
        if not self.approved_budget or self.approved_budget == 0:
            return None
        return (self.total_expenses / self.approved_budget) * 100

    @property
    def total_task_allocations(self):
        TaskCost = apps.get_model("scheduling", "TaskCost")
        return sum(tc.allocated_amount for tc in TaskCost.objects.filter(task__project=self))

    @property
    def remaining_budget(self):
        return (self.approved_budget or 0) - self.total_task_allocations

    # ----------------------------
    # Document Helper Properties
    # ----------------------------
    @property
    def contract_documents(self):
        """Get all contract documents for this project"""
        return self.documents.filter(document_type='CONTRACT', is_archived=False)

    @property
    def permit_documents(self):
        """Get all permit/license documents for this project"""
        return self.documents.filter(document_type='PERMIT', is_archived=False)

    @property
    def has_contract_document(self):
        """Check if project has at least one contract document"""
        return self.contract_documents.exists()

    @property
    def has_permit_document(self):
        """Check if project has at least one permit document"""
        return self.permit_documents.exists()

    @property
    def missing_mandatory_documents(self):
        """Get list of missing mandatory document types"""
        missing = []
        if not self.has_contract_document:
            missing.append('Contract Agreement')
        if not self.has_permit_document:
            missing.append('Permits & Licenses')
        return missing

    def save(self, *args, **kwargs):
        # --- Progress logic ---
        # Clamp progress between 0 and 100
        self.progress = max(0, min(self.progress, 100))
        self.is_completed = self.progress >= 100

        # --- Project ID logic ---
        is_new = self.pk is None
        super().save(*args, **kwargs)  # First save to get auto-incremented id

        if is_new and not self.project_id:
            prefix = self.project_source or "PRJ"
            self.project_id = f"{prefix}-{self.id:03d}"  # e.g., GC-001
            kwargs['force_insert'] = False
            super().save(*args, **kwargs)
        
    def update_progress_from_tasks(self):
        tasks = self.tasks.all()
        if tasks.exists():
            total_progress = sum(
            (task.progress or Decimal(0)) * (Decimal(task.weight) / Decimal(100))
            for task in tasks
            )
            self.progress = min(total_progress, Decimal(100))
        else:
            self.progress = Decimal(0)

    # Auto-update project status
        if self.progress >= 100:
            self.status = "CP"
        elif self.progress > 0:
            self.status = "OG"
        else:
            self.status = "PL"

        self.save(update_fields=["progress", "status"])
    
    # BOQ tracking fields for cost learning
    extracted_total_cost = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Total cost extracted from BOQ documents"
    )
    extracted_cost_breakdown = models.JSONField(
        null=True, 
        blank=True,
        help_text="Cost breakdown extracted from BOQ (materials, labor, etc.)"
    )
    boq_file_processed = models.BooleanField(
        default=False,
        help_text="Whether BOQ file has been processed for cost extraction"
    )
    cost_data_contributed = models.BooleanField(
        default=False,
        help_text="Whether this project's cost data has been contributed to ProjectType learning"
    )
    
    # BOQ detailed data storage
    boq_items = models.JSONField(
        null=True,
        blank=True,
        help_text="Detailed BOQ items with dependencies and breakdowns"
    )
    boq_dependencies = models.JSONField(
        null=True,
        blank=True,
        help_text="Dependency mapping for BOQ items"
    )
    boq_division_subtotals = models.JSONField(
        null=True,
        blank=True,
        help_text="Cost subtotals by division from BOQ data"
    )
    boq_project_info = models.JSONField(
        null=True,
        blank=True,
        help_text="Project information extracted from BOQ (floor area, etc.)"
    )
    floor_area = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Floor area in square meters"
    )
    project_role = models.CharField(
        max_length=20,
        choices=[
            ('general_contractor', 'General Contractor'),
            ('subcontractor', 'Subcontractor')
        ],
        default='general_contractor',
        help_text="Role of the company in this project"
    )
    
    # RFS file tracking
    rfs_file = models.FileField(
        upload_to='rfs_files/',
        null=True,
        blank=True,
        help_text="Auto-generated Request for Supplier file"
    )
        
#Temporary for projects that needs to be approved
class ProjectStaging(models.Model):
    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    project_data = models.JSONField()
    project_source = models.CharField(max_length=20, choices=[("GC", "General Contractor"), ("DC", "Direct Client")])
    project_id_placeholder = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=2, choices=[("PL", "Pending"), ("AP", "Approved"), ("RJ", "Rejected")], default="PL")
    submitted_at = models.DateTimeField(default=timezone.now)

    is_draft = models.BooleanField(default=False, help_text="True if this is a draft")
    submitted_for_approval = models.BooleanField(default=False, help_text="True if submitted for approval")
    approved_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staging_projects_approved",
        limit_choices_to={"role": "EG"}
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        if self.project_data and isinstance(self.project_data, dict):
            name = self.project_data.get("project_name", "Unnamed")
        else:
            name = "Unnamed"
        return f"{name} ({self.project_source_display})"


    @property
    def project_source_display(self):
        return dict([("GC", "General Contractor"), ("DC", "Direct Client")]).get(self.project_source, self.project_source)
    
    class Meta:
        ordering = ["-submitted_at"] 


class ProjectStagingHistory(models.Model):
    project_staging = models.ForeignKey("ProjectStaging", related_name="history_logs", on_delete=models.CASCADE)
    created_by = models.ForeignKey("authentication.UserProfile", on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=2, choices=[("PL","Pending"),("AP","Approved"),("RJ","Rejected")])
    comments = models.TextField(blank=True, null=True)  # optional notes from reviewer
    submitted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-submitted_at"]
        
class ProjectFile(models.Model):
    project = models.ForeignKey(ProjectProfile, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="project_files/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
class CostCategory(models.TextChoices):
    LABOR = "LAB", "Labor"
    MATERIALS = "MAT", "Materials"
    EQUIPMENT = "EQP", "Equipment"
    SUBCONTRACTOR = "SUB", "Subcontractor"
    MOBILIZATION = "MOB", "Mobilization"
    OTHER = "OTH", "Other"


# 1️⃣ Planned budget
class ProjectBudget(models.Model):
    project = models.ForeignKey("ProjectProfile", on_delete=models.CASCADE, related_name="budgets")
    
    # Use the existing ProjectScope model
    scope = models.ForeignKey(ProjectScope, on_delete=models.CASCADE, related_name="budget_categories")
    
    # Cost category within the scope
    category = models.CharField(max_length=3, choices=CostCategory.choices)
    category_other = models.CharField(max_length=255, blank=True, null=True, help_text="Specify if category is Other")
    
    planned_amount = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['scope', 'category']  # Prevent duplicate scope-category combinations
        ordering = ['scope__name', 'category']

    def __str__(self):
        return f"[BUDGET] {self.scope.name} > {self.get_category_display()} (₱{self.planned_amount:,.2f})"

    @property
    def total_allocated(self):
        """Calculate total amount allocated for this budget category"""
        return self.allocations.aggregate(total=models.Sum('amount'))['total'] or 0

    @property
    def remaining_amount(self):
        """Calculate remaining amount available for allocation"""
        return self.planned_amount - self.total_allocated

    @property
    def allocation_percentage(self):
        """Calculate percentage of budget that has been allocated"""
        if self.planned_amount > 0:
            return (self.total_allocated / self.planned_amount) * 100
        return 0

    @property
    def is_over_budget(self):
        """Check if allocations exceed planned amount"""
        return self.total_allocated > self.planned_amount



# 2️⃣ Actual expenditures (linked to tasks if needed)
class ProjectCost(models.Model):
    project = models.ForeignKey("ProjectProfile", on_delete=models.CASCADE, related_name="costs")
    category = models.CharField(max_length=3, choices=CostCategory.choices)
    description = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date_incurred = models.DateField(default=timezone.now)
    linked_task = models.ForeignKey(
        "scheduling.ProjectTask",
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_incurred"]

    def __str__(self):
        return f"[ACTUAL] {self.project.project_name} - {self.get_category_display()} ({self.amount})"

class FundAllocation(models.Model):
    project_budget = models.ForeignKey(
        "ProjectBudget", 
        on_delete=models.CASCADE,
        related_name="allocations"
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date_allocated = models.DateField(default=timezone.now)
    note = models.CharField(max_length=255, blank=True, null=True)

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ["-date_allocated"]
        
    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
        
    def restore(self):
        """Restore a soft-deleted allocation"""
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    def __str__(self):
        return f"[ALLOC] {self.project_budget.project.project_name} - {self.project_budget.get_category_display()} ({self.amount})"


class SubcontractorExpense(models.Model):
    """Detailed tracking of subcontractor expenses"""
    project = models.ForeignKey(ProjectProfile, on_delete=models.CASCADE, related_name='subcontractor_expenses')
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='subcontractor_details', null=True, blank=True)

    # Subcontractor information
    subcontractor_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200, blank=True)
    contact_number = models.CharField(max_length=50, blank=True)

    # Contract details
    contract_number = models.CharField(max_length=100, blank=True)
    scope_of_work = models.TextField()
    contract_amount = models.DecimalField(max_digits=15, decimal_places=2)

    # Payment tracking
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    payment_date = models.DateField(null=True, blank=True)

    # Dates
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)

    # Status
    STATUS_CHOICES = [
        ('PEND', 'Pending'),
        ('PROG', 'In Progress'),
        ('COMP', 'Completed'),
        ('CANC', 'Cancelled'),
    ]
    status = models.CharField(max_length=4, choices=STATUS_CHOICES, default='PEND')

    # Documentation
    contract_file = models.FileField(upload_to='subcontractor_contracts/', blank=True, null=True)

    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['subcontractor_name']),
        ]

    def __str__(self):
        return f"{self.project.project_name} - {self.subcontractor_name}"

    @property
    def remaining_balance(self):
        """Calculate remaining balance to be paid"""
        return self.contract_amount - self.amount_paid

    @property
    def payment_percentage(self):
        """Calculate percentage of contract amount paid"""
        if self.contract_amount > 0:
            return (self.amount_paid / self.contract_amount) * 100
        return 0


class SubcontractorPayment(models.Model):
    """Track individual payments to subcontractors (supports milestone-based payments)"""
    PAYMENT_METHODS = [
        ('CHECK', 'Check'),
        ('BANK', 'Bank Transfer'),
        ('CASH', 'Cash'),
        ('CREDIT', 'Credit/Debit Card'),
        ('OTHER', 'Other'),
    ]

    PAYMENT_STATUS = [
        ('PEND', 'Pending Approval'),
        ('APPR', 'Approved'),
        ('PAID', 'Paid'),
        ('CANC', 'Cancelled'),
    ]

    subcontractor_expense = models.ForeignKey(
        SubcontractorExpense,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    payment_number = models.PositiveIntegerField(help_text="Sequential payment number")
    milestone_description = models.TextField(help_text="What milestone/work phase this payment covers")

    # Payment details
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='BANK')
    payment_date = models.DateField()
    reference_number = models.CharField(max_length=100, blank=True, help_text="Check number, transaction ID, etc.")

    # Status and approval
    status = models.CharField(max_length=4, choices=PAYMENT_STATUS, default='PEND')
    approved_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_payments'
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    # Documentation
    receipt_file = models.FileField(upload_to='subcontractor_receipts/', blank=True, null=True)
    invoice_file = models.FileField(upload_to='subcontractor_invoices/', blank=True, null=True)

    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='created_payments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['subcontractor_expense', 'payment_number']
        unique_together = ['subcontractor_expense', 'payment_number']
        indexes = [
            models.Index(fields=['subcontractor_expense', 'status']),
            models.Index(fields=['payment_date']),
        ]

    def __str__(self):
        return f"{self.subcontractor_expense.subcontractor_name} - Payment #{self.payment_number} (₱{self.amount:,.2f})"

    def save(self, *args, **kwargs):
        # Auto-set payment number if not provided
        if not self.payment_number:
            last_payment = SubcontractorPayment.objects.filter(
                subcontractor_expense=self.subcontractor_expense
            ).order_by('-payment_number').first()
            self.payment_number = (last_payment.payment_number + 1) if last_payment else 1

        # Update approval timestamp
        if self.status == 'APPR' and not self.approved_at and self.approved_by:
            self.approved_at = timezone.now()

        super().save(*args, **kwargs)

        # Update parent SubcontractorExpense total
        self._update_parent_totals()

    def _update_parent_totals(self):
        """Update the parent SubcontractorExpense amount_paid based on approved/paid payments"""
        total_paid = self.subcontractor_expense.payments.filter(
            status__in=['APPR', 'PAID']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        self.subcontractor_expense.amount_paid = total_paid
        self.subcontractor_expense.save(update_fields=['amount_paid'])




class ProjectDocument(models.Model):
    """Enhanced document attachment system for projects"""
    DOCUMENT_TYPES = [
        ('CONTRACT', 'Contract Agreement'),
        ('PERMIT', 'Permit/License'),
        ('PROGRESS', 'Progress Report'),
        ('COSTING', 'Costing Proof'),
        ('INVOICE', 'Invoice'),
        ('RECEIPT', 'Receipt'),
        ('TECHNICAL', 'Technical Drawing'),
        ('PHOTO', 'Project Photo'),
        ('QUOTATION', 'Supplier Quotation'),
        ('RFS', 'Request for Supplier'),
        ('OTHER', 'Other'),
    ]

    PROJECT_STAGES = [
        ('INIT', 'Initiation'),
        ('PLAN', 'Planning'),
        ('EXEC', 'Execution'),
        ('MONITOR', 'Monitoring'),
        ('CLOSE', 'Closing'),
    ]

    APPROVAL_STATUS = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('REVISION', 'Needs Revision'),
    ]

    project = models.ForeignKey(
        ProjectProfile,
        on_delete=models.CASCADE,
        related_name='documents',
        null=True,
        blank=True
    )
    # Support for pending projects
    project_staging = models.ForeignKey(
        ProjectStaging,
        on_delete=models.CASCADE,
        related_name='documents',
        null=True,
        blank=True,
        help_text="Link to pending project if document uploaded before approval"
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_type_other = models.CharField(max_length=100, blank=True, help_text="Specify if type is Other")
    project_stage = models.CharField(max_length=10, choices=PROJECT_STAGES)

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='project_documents/')
    file_size = models.PositiveIntegerField(help_text="File size in bytes", null=True, blank=True)

    # Versioning
    version = models.CharField(max_length=20, default='1.0')
    replaces = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replacements',
        help_text="Previous version of this document"
    )
    version_notes = models.TextField(blank=True, help_text="What changed in this version")

    # Approval workflow (for GC approving Subcon documents)
    approval_status = models.CharField(max_length=10, choices=APPROVAL_STATUS, default='PENDING')
    approved_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_documents'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, help_text="Reason for rejection or revision request")

    # Metadata
    uploaded_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_mandatory = models.BooleanField(default=False, help_text="Required document for this project")
    is_archived = models.BooleanField(default=False)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags for searchability")

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['project', 'document_type']),
            models.Index(fields=['project', 'project_stage']),
            models.Index(fields=['is_mandatory', 'is_archived']),
        ]

    def __str__(self):
        return f"{self.project.project_name} - {self.title}"

    def save(self, *args, **kwargs):
        # Calculate file size if not set
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except:
                pass
        super().save(*args, **kwargs)

    @property
    def file_size_mb(self):
        """Return file size in MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0

    @property
    def file_extension(self):
        """Get file extension"""
        if self.file:
            import os
            return os.path.splitext(self.file.name)[1].lower()
        return ''


class SupplierQuotation(models.Model):
    """Supplier quotations for projects"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    # Use a generic approach to support both ProjectProfile and ProjectStaging
    project_id = models.PositiveIntegerField(help_text="Project ID")
    project_type = models.CharField(
        max_length=20,
        choices=[
            ('profile', 'ProjectProfile'),
            ('staging', 'ProjectStaging'),
        ],
        help_text="Type of project (profile or staging)"
    )
    supplier_name = models.CharField(
        max_length=200,
        help_text="Name of the supplier"
    )
    quotation_file = models.FileField(
        upload_to='quotations/',
        help_text="Uploaded quotation file (PDF or Excel)"
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total amount quoted (can be manual or auto-calculated)"
    )
    date_submitted = models.DateTimeField(
        auto_now_add=True,
        help_text="When this quotation was submitted"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text="Current status of this quotation"
    )
    uploaded_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_quotations',
        help_text="User who uploaded this quotation"
    )
    approved_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_quotations',
        help_text="User who approved this quotation"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this quotation was approved"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about this quotation"
    )
    
    class Meta:
        ordering = ['-date_submitted']
        verbose_name = 'Supplier Quotation'
        verbose_name_plural = 'Supplier Quotations'
        indexes = [
            models.Index(fields=['project_id', 'project_type', 'status']),
            models.Index(fields=['supplier_name']),
        ]
    
    @property
    def project(self):
        """Get the actual project object"""
        if self.project_type == 'profile':
            from .models import ProjectProfile
            return ProjectProfile.objects.get(pk=self.project_id)
        else:
            from .models import ProjectStaging
            return ProjectStaging.objects.get(pk=self.project_id)
    
    def __str__(self):
        try:
            project_name = self.project.project_data.get('project_name', 'Unknown Project')
        except:
            project_name = f"Project {self.project_id}"
        amount_str = f"₱{self.total_amount:,.2f}" if self.total_amount else "₱0.00"
        return f"{self.supplier_name} - {project_name} ({amount_str})"
    
    def clean(self):
        """Validate quotation constraints"""
        from django.core.exceptions import ValidationError
        
        # Check max 5 quotations per project
        if not self.pk:  # Only for new instances
            existing_count = SupplierQuotation.objects.filter(
                project_id=self.project_id,
                project_type=self.project_type
            ).count()
            if existing_count >= 5:
                raise ValidationError("Maximum 5 quotations allowed per project.")
        
        # Check only one approved quotation per project
        if self.status == 'APPROVED':
            existing_approved = SupplierQuotation.objects.filter(
                project_id=self.project_id,
                project_type=self.project_type,
                status='APPROVED'
            ).exclude(pk=self.pk)
            if existing_approved.exists():
                raise ValidationError("Only one quotation can be approved per project.")
    
    def save(self, *args, **kwargs):
        # Set approval timestamp
        if self.status == 'APPROVED' and not self.approved_at and self.approved_by:
            from django.utils import timezone
            self.approved_at = timezone.now()
        
        # Auto-reject other quotations when this one is approved
        if self.status == 'APPROVED' and self.pk:
            SupplierQuotation.objects.filter(
                project_id=self.project_id,
                project_type=self.project_type,
                status='PENDING'
            ).exclude(pk=self.pk).update(status='REJECTED')
        
        super().save(*args, **kwargs)
    
    @property
    def file_extension(self):
        """Get file extension"""
        if self.quotation_file:
            import os
            return os.path.splitext(self.quotation_file.name)[1].lower()
        return ''
    
    @property
    def is_excel(self):
        """Check if file is Excel format"""
        return self.file_extension in ['.xlsx', '.xls']
    
    @property
    def is_pdf(self):
        """Check if file is PDF format"""
        return self.file_extension == '.pdf'


