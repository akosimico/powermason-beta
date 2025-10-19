from django.contrib import admin
from .models import Notification, NotificationStatus

class NotificationStatusInline(admin.TabularInline):
    model = NotificationStatus
    extra = 0
    readonly_fields = ('user', 'is_read', 'cleared')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('message', 'role', 'created_at', 'archived')
    list_filter = ('role', 'archived', 'created_at')
    search_fields = ('message',)
    inlines = [NotificationStatusInline]


@admin.register(NotificationStatus)
class NotificationStatusAdmin(admin.ModelAdmin):
    list_display = ('notification', 'user', 'is_read', 'cleared')
    list_filter = ('is_read', 'cleared')
    search_fields = ('notification__message', 'user__user__username')
