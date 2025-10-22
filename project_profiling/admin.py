from django.contrib import admin
from .models import (
    ProjectProfile, ProjectBudget, ProjectCost, ProjectStaging,
    ProjectType, Expense, SubcontractorExpense, SubcontractorPayment,
    MobilizationCost, ProjectDocument, SupplierQuotation
)

@admin.register(ProjectProfile)
class ProjectProfileAdmin(admin.ModelAdmin):
    list_display = (
        "project_name",              # changed from project_title
        "project_id",
        "project_type",
        "project_manager",
        "site_engineer",  
        "start_date",
        "target_completion_date",    # changed from end_date
        "approved_budget",
    )
    list_filter = ('project_source', 'project_type', 'status')
    search_fields = (
        'project_id', 
        'project_name', 
        'client_name', 
        'gc_company_name'
    )
    ordering = ('-created_at',)
    
@admin.register(ProjectBudget)
class ProjectBudgetAdmin(admin.ModelAdmin):
    list_display = ("project", "category", "planned_amount")
    list_filter = ("category", "project")
    search_fields = ("project__name",)
    ordering = ("project", "category")


@admin.register(ProjectCost)
class ProjectCostAdmin(admin.ModelAdmin):
    list_display = ("project", "category", "description", "amount", "date_incurred", "linked_task", "created_at")
    list_filter = ("category", "date_incurred", "project")
    search_fields = ("project__name", "description", "linked_task__task_name")
    date_hierarchy = "date_incurred"
    ordering = ("-date_incurred",)

@admin.register(ProjectStaging)
class ProjectStagingAdmin(admin.ModelAdmin):
    list_display = ['id', 'project_source', 'created_by', 'submitted_at', 'status']
    
    
@admin.register(ProjectType)
class ProjectTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
        "usage_count",
    )
    list_filter = ("is_active", "created_at", "updated_at")
    search_fields = ("name", "code", "description")
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at", "usage_count")

    fieldsets = (
        (None, {
            "fields": ("name", "code", "description", "is_active")
        }),
        ("Audit Info", {
            "fields": ("created_by", "created_at", "updated_at", "usage_count"),
        }),
    )

    def usage_count(self, obj):
        return obj.get_usage_count()
    usage_count.short_description = "Usage Count"
    
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        'project',
        'budget_category',
        'expense_type',
        'expense_other',
        'amount',
        'vendor',
        'expense_date',
        'created_by',
        'created_at',
    )
    
    list_filter = (
        'expense_type',
        'project',
        'budget_category',
        'expense_date',
    )
    
    search_fields = (
        'project__name',
        'budget_category__name',
        'vendor',
        'receipt_number',
        'description',
        'expense_other',
    )
    
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {
            'fields': (
                'project',
                'budget_category',
                'expense_type',
                'expense_other',
                'amount',
                'vendor',
                'receipt_number',
                'expense_date',
                'description',
            )
        }),
        ('Audit Info', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user.userprofile  # Assuming UserProfile is linked via OneToOne to User
        super().save_model(request, obj, form, change)


@admin.register(SubcontractorExpense)
class SubcontractorExpenseAdmin(admin.ModelAdmin):
    list_display = [
        'subcontractor_name', 'project', 'contract_amount',
        'amount_paid', 'remaining_balance', 'payment_percentage', 'status'
    ]
    list_filter = ['status', 'start_date', 'completion_date']
    search_fields = ['subcontractor_name', 'project__project_name', 'contact_person']
    date_hierarchy = 'start_date'
    ordering = ['-created_at']

    fieldsets = (
        ('Subcontractor Information', {
            'fields': ('project', 'subcontractor_name', 'contact_person', 'contact_number')
        }),
        ('Contract Details', {
            'fields': ('contract_number', 'scope_of_work', 'contract_amount', 'contract_file')
        }),
        ('Payment Tracking', {
            'fields': ('amount_paid', 'payment_date')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'completion_date', 'status')
        }),
        ('Additional Information', {
            'fields': ('notes', 'expense'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    readonly_fields = ['created_at', 'updated_at']

    def remaining_balance(self, obj):
        return f"₱{obj.remaining_balance:,.2f}"
    remaining_balance.short_description = 'Remaining Balance'

    def payment_percentage(self, obj):
        return f"{obj.payment_percentage:.1f}%"
    payment_percentage.short_description = 'Payment %'


@admin.register(SubcontractorPayment)
class SubcontractorPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'payment_number_display', 'subcontractor_expense', 'amount',
        'payment_method', 'payment_date', 'status', 'approved_by'
    ]
    list_filter = ['status', 'payment_method', 'payment_date', 'created_at']
    search_fields = ['subcontractor_expense__subcontractor_name', 'milestone_description', 'reference_number']
    date_hierarchy = 'payment_date'
    ordering = ['-payment_date', '-payment_number']

    fieldsets = (
        ('Payment Information', {
            'fields': ('subcontractor_expense', 'payment_number', 'milestone_description')
        }),
        ('Payment Details', {
            'fields': ('amount', 'payment_method', 'payment_date', 'reference_number')
        }),
        ('Documentation', {
            'fields': ('receipt_file', 'invoice_file')
        }),
        ('Approval', {
            'fields': ('status', 'approved_by', 'approved_at')
        }),
        ('Additional', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    readonly_fields = ['payment_number', 'approved_at', 'created_at', 'updated_at']

    def payment_number_display(self, obj):
        return f"Payment #{obj.payment_number}"
    payment_number_display.short_description = 'Payment #'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user.userprofile
        super().save_model(request, obj, form, change)


@admin.register(MobilizationCost)
class MobilizationCostAdmin(admin.ModelAdmin):
    list_display = [
        'project', 'category', 'description_short', 'quantity',
        'unit', 'unit_cost', 'total_cost_display', 'date_incurred'
    ]
    list_filter = ['category', 'date_incurred', 'project']
    search_fields = ['project__project_name', 'description', 'vendor_name']
    date_hierarchy = 'date_incurred'
    ordering = ['-date_incurred']

    fieldsets = (
        ('Project & Category', {
            'fields': ('project', 'category', 'description')
        }),
        ('Cost Details', {
            'fields': ('quantity', 'unit', 'unit_cost')
        }),
        ('Vendor Information', {
            'fields': ('vendor_name', 'invoice_number', 'invoice_file'),
            'classes': ('collapse',)
        }),
        ('Additional', {
            'fields': ('date_incurred', 'notes'),
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    readonly_fields = ['created_at', 'updated_at']

    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'

    def total_cost_display(self, obj):
        return f"₱{obj.total_cost:,.2f}"
    total_cost_display.short_description = 'Total Cost'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user.userprofile
        super().save_model(request, obj, form, change)


@admin.register(ProjectDocument)
class ProjectDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'project', 'document_type', 'project_stage',
        'version', 'approval_status', 'file_size_display', 'uploaded_by', 'uploaded_at', 'is_mandatory'
    ]
    list_filter = ['document_type', 'project_stage', 'approval_status', 'is_mandatory', 'is_archived', 'uploaded_at']
    search_fields = ['title', 'description', 'project__project_name', 'tags']
    date_hierarchy = 'uploaded_at'
    ordering = ['-uploaded_at']

    fieldsets = (
        ('Document Information', {
            'fields': ('project', 'document_type', 'document_type_other', 'project_stage', 'title', 'description')
        }),
        ('File', {
            'fields': ('file', 'file_size')
        }),
        ('Version Control', {
            'fields': ('version', 'replaces', 'version_notes')
        }),
        ('Approval Workflow', {
            'fields': ('approval_status', 'approved_by', 'approved_at', 'rejection_reason')
        }),
        ('Settings', {
            'fields': ('is_mandatory', 'is_archived', 'tags')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'uploaded_at'),
            'classes': ('collapse',)
        })
    )

    readonly_fields = ['uploaded_at', 'approved_at', 'file_size']

    def file_size_display(self, obj):
        return f"{obj.file_size_mb} MB"
    file_size_display.short_description = 'File Size'


@admin.register(SupplierQuotation)
class SupplierQuotationAdmin(admin.ModelAdmin):
    list_display = [
        'supplier_name', 'project_display', 'total_amount_display', 
        'status', 'date_submitted', 'approved_by', 'approved_at'
    ]
    list_filter = ['status', 'project_type', 'date_submitted', 'approved_at']
    search_fields = ['supplier_name', 'project_id', 'quotation_file']
    date_hierarchy = 'date_submitted'
    ordering = ['-date_submitted']
    
    fieldsets = (
        ('Quotation Information', {
            'fields': ('supplier_name', 'quotation_file', 'total_amount', 'date_submitted')
        }),
        ('Project Details', {
            'fields': ('project_id', 'project_type')
        }),
        ('Approval', {
            'fields': ('status', 'approved_by', 'approved_at')
        }),
        ('Additional', {
            'fields': ('notes', 'uploaded_by'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['date_submitted', 'approved_at', 'uploaded_by']
    
    def project_display(self, obj):
        """Display project information based on project_type"""
        if obj.project_type == 'profile':
            try:
                from .models import ProjectProfile
                project = ProjectProfile.objects.get(id=obj.project_id)
                return f"{project.project_name} (Profile)"
            except:
                return f"Project {obj.project_id} (Profile)"
        elif obj.project_type == 'staging':
            try:
                from .models import ProjectStaging
                project = ProjectStaging.objects.get(id=obj.project_id)
                project_name = project.project_data.get('project_name', 'Unknown') if project.project_data else 'Unknown'
                return f"{project_name} (Staging)"
            except:
                return f"Project {obj.project_id} (Staging)"
        return f"Project {obj.project_id} ({obj.project_type})"
    project_display.short_description = 'Project'
    
    def total_amount_display(self, obj):
        if obj.total_amount:
            return f"₱{obj.total_amount:,.2f}"
        return "₱0.00"
    total_amount_display.short_description = 'Total Amount'
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            # Set uploaded_by for new quotations
            obj.uploaded_by = request.user.userprofile
        super().save_model(request, obj, form, change)