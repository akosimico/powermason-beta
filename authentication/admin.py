from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, UserProfile


# Inline profile in User admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"


# Custom User admin
class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    fieldsets = (
        (None, {"fields": ("email", "password", "first_name", "last_name")}),  # 👈 updated to first_name, last_name
        ("Permissions", {
            "fields": (
                "is_active", "is_staff", "is_superuser", "groups", "user_permissions"
            )
        }),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2"),  # 👈 updated to first_name, last_name
        }),
    )
    list_display = ("email", "get_full_name", "is_staff", "is_superuser")  # 👈 use get_full_name method
    search_fields = ("email", "first_name", "last_name")  # 👈 search both name fields
    ordering = ("email",)

    def get_full_name(self, obj):
        """Display full name in admin list"""
        return f"{obj.first_name} {obj.last_name}".strip()
    get_full_name.short_description = "Full Name"


# Register CustomUser with the new admin
admin.site.register(CustomUser, CustomUserAdmin)


# UserProfile admin (updated search fields)
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "is_archived", "updated_at")
    list_filter = ("role", "is_archived")
    search_fields = ("user__email", "user__first_name", "user__last_name")  # 👈 updated search fields