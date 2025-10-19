from django.contrib import admin
from .models import XeroConnection

@admin.register(XeroConnection)
class XeroConnectionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "tenant_id",
        "is_valid_display",
        "expires_at",
        "created_at",
        "updated_at",
    )
    search_fields = ("user__username", "tenant_id")
    list_filter = ("created_at", "updated_at", "expires_at")
    readonly_fields = ("created_at", "updated_at")

    def is_valid_display(self, obj):
        return obj.is_valid()
    is_valid_display.boolean = True
    is_valid_display.short_description = "Valid?"

