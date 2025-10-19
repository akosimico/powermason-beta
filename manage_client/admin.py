from django.contrib import admin
from django.utils.html import format_html
from .models import Client
from project_profiling.models import ProjectType


# manage_client/admin.py
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "contact_name",
        "email",
        "phone",
        "client_type",
        "is_active",
        "has_contract",  # Added contract indicator
        "project_count",
        "created_by",
        "created_at",
    )
    list_filter = ("client_type", "is_active", "created_at")
    search_fields = ("company_name", "contact_name", "email", "phone", "city", "state")
    readonly_fields = ("created_at", "updated_at", "full_address", "project_count", "contract_display")

    fieldsets = (
        ("Basic Information", {
            "fields": (
                "company_name",
                "contact_name",
                "email",
                "phone",
                "client_type",
                "is_active",
                "project_types",
            )
        }),
        ("Address", {
            "fields": ("address", "city", "state", "zip_code", "full_address")
        }),
        ("Contract & Documents", {
            "fields": ("contract", "contract_display")
        }),
        ("Additional Info", {"fields": ("notes",)}),
        ("Xero Integration", {
            "fields": ("xero_contact_id", "xero_last_sync"),
            "classes": ("collapse",)  # Make this section collapsible
        }),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at")}),
    )

    def project_count(self, obj):
        return obj.get_project_count()  # Use the model method if it exists
    project_count.short_description = "Projects"

    def full_address(self, obj):
        return obj.get_full_address()
    full_address.short_description = "Full Address"

    def has_contract(self, obj):
        """Display contract status with icon"""
        if obj.contract:
            return format_html(
                '<span style="color: green;">📄 Yes</span>'
            )
        return format_html(
            '<span style="color: #999;">❌ No</span>'
        )
    has_contract.short_description = "Contract"
    has_contract.admin_order_field = "contract"  # Allow sorting by this field

    def contract_display(self, obj):
        """Display contract information with download link"""
        if obj.contract:
            return format_html(
                '<a href="{}" target="_blank" style="color: #0066cc; text-decoration: none;">'
                '📄 {} (Download)</a><br>'
                '<small style="color: #666;">Uploaded: {}</small>',
                obj.contract.url,
                obj.contract.name.split('/')[-1],  # Get just the filename
                obj.created_at.strftime('%Y-%m-%d %H:%M') if obj.created_at else 'Unknown'
            )
        return format_html(
            '<span style="color: #999; font-style: italic;">No contract uploaded</span>'
        )
    contract_display.short_description = "Contract File"

    # Optional: Add custom actions
    actions = ['export_clients_with_contracts']

    def export_clients_with_contracts(self, request, queryset):
        """Custom admin action to export clients that have contracts"""
        clients_with_contracts = queryset.filter(contract__isnull=False)
        # You could implement CSV export or other functionality here
        self.message_user(
            request, 
            f"Found {clients_with_contracts.count()} clients with contracts out of {queryset.count()} selected."
        )
    export_clients_with_contracts.short_description = "Check contract status for selected clients"