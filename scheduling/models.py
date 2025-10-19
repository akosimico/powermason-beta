from django.db import models
from authentication.models import UserProfile      
from decimal import Decimal

class ProjectScope(models.Model):
    project = models.ForeignKey(
        "project_profiling.ProjectProfile", 
        on_delete=models.CASCADE, 
        related_name="scopes"
    )
    name = models.CharField(max_length=255)
    weight = models.DecimalField(
        max_digits=5, decimal_places=2, 
        help_text="Weight contribution to project (%)"
    )
    is_deleted = models.BooleanField(default=False)  # Add this field
    
    def __str__(self):
        return f"{self.name} ({self.project.project_name})"
    
    @property
    def has_tasks(self):
        # Check if this scope has any associated tasks
        # Adjust the related name based on your Task model
        return hasattr(self, 'tasks') and self.tasks.exists()
    

class ProjectTask(models.Model):
    STATUS_CHOICES = [
        ("PL", "Planned"),
        ("OG", "Ongoing"),
        ("CP", "Completed"),
    ]

    project = models.ForeignKey(
        "project_profiling.ProjectProfile", 
        on_delete=models.CASCADE, 
        related_name="tasks"
    )
    task_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    scope = models.ForeignKey(ProjectScope, on_delete=models.CASCADE, related_name="tasks")

    # Assigned to PM for reporting only
    assigned_to = models.ForeignKey(
        UserProfile, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Project Manager responsible for updating this task"
    )
    
    start_date = models.DateField()
    end_date = models.DateField()
    duration_days = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    manhours = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Weight relative to scope
    weight = models.DecimalField(
        max_digits=5, decimal_places=2, 
        help_text="Weight of task relative to its scope (%)"
    )
    progress = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Progress % reported by Project Manager"
    )
    dependencies = models.ManyToManyField("self", symmetrical=False, blank=True)
    is_completed = models.BooleanField(default=False)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default="PL") 

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.task_name} ({self.project.project_name})"

    def save(self, *args, **kwargs):
        # Auto-calculate duration_days if start and end dates exist
        if self.start_date and self.end_date:
            self.duration_days = (self.end_date - self.start_date).days + 1  # inclusive

        # Auto-calculate manhours (1 worker, 8 hours/day)
        if self.duration_days:
            self.manhours = self.duration_days * 8

        # Auto-mark task status based on progress
        if self.progress >= 100:
            self.is_completed = True
            self.status = "CP"
        elif self.progress > 0:
            self.is_completed = False
            self.status = "OG"
        else:
            self.is_completed = False
            self.status = "PL"

        super().save(*args, **kwargs)

    @staticmethod
    def calculate_project_progress(project):
        """
        Calculate overall project progress based on scope weight and task weights.
        """
        total_progress = 0
        for scope in project.scopes.all():
            for task in scope.tasks.all():
                task_contrib = (task.progress or 0)/100 * (float(task.weight)/100) * float(scope.weight)
                total_progress += task_contrib
        return min(total_progress, 100)  # cap at 100%

    def update_progress_from_tasks(self):
        """
        Updates task status and overall project progress.
        Only PM updates task progress.
        """
        # Update task status
        if self.progress >= 100:
            self.is_completed = True
            self.status = "CP"
        elif self.progress > 0:
            self.is_completed = False
            self.status = "OG"
        else:
            self.is_completed = False
            self.status = "PL"

        self.save(update_fields=["progress", "status", "is_completed"])

        # Update overall project progress
        project_progress = self.calculate_project_progress(self.project)
        self.project.progress = project_progress
        self.project.save(update_fields=["progress"])
        return project_progress


class ProgressReport(models.Model):
    project = models.ForeignKey( "project_profiling.ProjectProfile", on_delete=models.CASCADE, related_name="progress_reports")
    report_date = models.CharField(max_length=50, null=True, blank=True)  # can change to DateField if your PDF always has proper dates
    accomplished_to_date = models.CharField(max_length=50, null=True, blank=True)
    accomplished_before = models.CharField(max_length=50, null=True, blank=True)
    accomplished_this_period = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.project_code} - {self.report_date}"
    
    
class ProgressUpdate(models.Model):
    STATUS_CHOICES = [
        ('P', 'Pending'),
        ('A', 'Approved'),
        ('R', 'Rejected'),
    ]

    task = models.ForeignKey(ProjectTask, on_delete=models.CASCADE, related_name="updates")
    reported_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name="updates_made")
    
    progress_percent = models.DecimalField(max_digits=5, decimal_places=2)  # e.g., 45.00
    remarks = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    reviewed_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="updates_reviewed")
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task.task_name} - {self.progress_percent}% ({self.get_status_display()})"

class ProgressFile(models.Model):
    update = models.ForeignKey(
    ProgressUpdate, 
    on_delete=models.CASCADE, 
    related_name="attachments",
    null=True, 
    blank=True
)
    file = models.FileField(upload_to="progress_proofs/")
    uploaded_at = models.DateTimeField(auto_now_add=True)


class SystemReport(models.Model):
    REPORT_TYPES = [
        ('D', 'Daily'),
        ('W', 'Weekly'),
        ('M', 'Monthly'),
        ('O', 'On-Demand'),
    ]

    project = models.ForeignKey( "project_profiling.ProjectProfile", on_delete=models.CASCADE, related_name="system_reports")
    report_type = models.CharField(max_length=1, choices=REPORT_TYPES)
    file = models.FileField(upload_to="auto_reports/")
    generated_at = models.DateTimeField(auto_now_add=True)

class ScopeBudget(models.Model):
    """Budget allocation for project scopes"""
    project = models.ForeignKey(
        "project_profiling.ProjectProfile",
        on_delete=models.CASCADE,
        related_name="scope_budgets"
    )
    scope = models.ForeignKey(
        ProjectScope,
        on_delete=models.CASCADE,
        related_name="budget"
    )
    allocated_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Budget allocated to this scope"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Scope Budget"
        verbose_name_plural = "Scope Budgets"
        unique_together = ['project', 'scope']

    def __str__(self):
        return f"{self.scope.name} - ₱{self.allocated_amount:,.2f}"

    @property
    def allocated_to_tasks(self):
        """Calculate total amount allocated to tasks in this scope"""
        from django.db.models import Sum
        total = self.scope.tasks.aggregate(
            total=Sum('task_costs__allocated_amount')
        )['total'] or 0
        return total

    @property
    def remaining_budget(self):
        """Calculate remaining budget for this scope"""
        return self.allocated_amount - self.allocated_to_tasks

    @property
    def utilization_percentage(self):
        """Calculate budget utilization percentage"""
        if self.allocated_amount == 0:
            return 0
        return (self.allocated_to_tasks / self.allocated_amount) * 100


class TaskCost(models.Model):
    task = models.ForeignKey(
        "scheduling.ProjectTask",
        on_delete=models.CASCADE,
        related_name="task_costs"
    )
    cost = models.ForeignKey(
        "project_profiling.ProjectCost",
        on_delete=models.CASCADE,
        related_name="task_costs"
    )
    allocated_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Prevent over-allocation
        if self.allocated_amount > (self.cost.amount or 0):
            raise ValueError("Allocated amount exceeds available cost")
        
        # Check scope budget limits
        scope_budget = ScopeBudget.objects.filter(
            project=self.task.project,
            scope=self.task.scope
        ).first()
        
        if scope_budget:
            current_allocated = scope_budget.allocated_to_tasks
            if self.pk:  # Updating existing allocation
                old_allocation = TaskCost.objects.get(pk=self.pk).allocated_amount
                current_allocated -= old_allocation
            
            if current_allocated + self.allocated_amount > scope_budget.allocated_amount:
                raise ValueError(f"Allocation exceeds scope budget of ₱{scope_budget.allocated_amount:,.2f}")
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.task} - {self.allocated_amount}/{self.cost.amount}"


# ========================================
# RESOURCE ALLOCATION MODELS
# Link materials, equipment, and manpower to tasks
# ========================================

class TaskMaterial(models.Model):
    """Materials allocated to a specific task"""
    task = models.ForeignKey(
        ProjectTask,
        on_delete=models.CASCADE,
        related_name="allocated_materials"
    )
    material = models.ForeignKey(
        "materials_equipment.Material",
        on_delete=models.CASCADE,
        related_name="task_allocations"
    )
    quantity_needed = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Quantity of this material needed for this task"
    )
    unit_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Cost per unit at time of allocation"
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Task Material Allocation"
        verbose_name_plural = "Task Material Allocations"

    @property
    def total_cost(self):
        return self.quantity_needed * self.unit_cost

    def __str__(self):
        return f"{self.task.task_name} - {self.material.name} ({self.quantity_needed} {self.material.unit})"


class TaskEquipment(models.Model):
    """Equipment allocated to a specific task"""
    ALLOCATION_TYPE = [
        ('RENTAL', 'Rental'),
        ('OWNED', 'Owned/Company'),
    ]

    task = models.ForeignKey(
        ProjectTask,
        on_delete=models.CASCADE,
        related_name="allocated_equipment"
    )
    equipment = models.ForeignKey(
        "materials_equipment.Equipment",
        on_delete=models.CASCADE,
        related_name="task_allocations"
    )
    allocation_type = models.CharField(max_length=10, choices=ALLOCATION_TYPE)
    quantity = models.IntegerField(default=1, help_text="Number of units needed")
    days_needed = models.IntegerField(
        help_text="Number of days equipment is needed for this task"
    )
    daily_rate = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Daily rental/usage cost"
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Task Equipment Allocation"
        verbose_name_plural = "Task Equipment Allocations"
        unique_together = ['task', 'equipment']

    @property
    def total_cost(self):
        return self.quantity * self.days_needed * self.daily_rate

    def __str__(self):
        return f"{self.task.task_name} - {self.equipment.name} x{self.quantity} ({self.days_needed} days)"


class TaskManpower(models.Model):
    """Manpower/Labor allocated to a specific task"""
    LABOR_TYPE = [
        ('SKILLED', 'Skilled Labor'),
        ('UNSKILLED', 'Unskilled Labor'),
        ('ENGINEER', 'Engineer'),
        ('FOREMAN', 'Foreman'),
        ('OPERATOR', 'Equipment Operator'),
    ]

    task = models.ForeignKey(
        ProjectTask,
        on_delete=models.CASCADE,
        related_name="allocated_manpower"
    )
    labor_type = models.CharField(max_length=20, choices=LABOR_TYPE)
    description = models.CharField(
        max_length=255,
        help_text="Description of labor role (e.g., 'Carpenter', 'Mason', 'Electrician')"
    )
    number_of_workers = models.IntegerField(default=1)
    daily_rate = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Daily wage per worker"
    )
    days_needed = models.IntegerField(
        help_text="Number of days this labor is needed"
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Task Manpower Allocation"
        verbose_name_plural = "Task Manpower Allocations"

    @property
    def total_cost(self):
        return self.number_of_workers * self.daily_rate * self.days_needed

    @property
    def total_manhours(self):
        """Calculate total manhours (workers × days × 8 hrs/day)"""
        return self.number_of_workers * self.days_needed * 8

    def __str__(self):
        return f"{self.task.task_name} - {self.get_labor_type_display()}: {self.description} x{self.number_of_workers}"
