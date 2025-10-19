from .models import Notification, NotificationStatus

def unread_notifications(request):
    if request.user.is_authenticated and hasattr(request.user, "userprofile"):
        profile = request.user.userprofile

        notifications = Notification.objects.filter(
            notificationstatus__user=profile,
            notificationstatus__cleared=False
        ).prefetch_related('notificationstatus_set').order_by('-created_at')

        unread_count = NotificationStatus.objects.filter(
            user=profile,
            is_read=False,
            cleared=False
        ).count()

        # Annotate each notification with is_read_for_user
        for notif in notifications:
            try:
                status = notif.notificationstatus_set.get(user=profile)
                notif.is_read_for_user = status.is_read
            except NotificationStatus.DoesNotExist:
                notif.is_read_for_user = True  

    else:
        notifications = []
        unread_count = 0

    return {
        "notifications": notifications,
        "unread_count": unread_count
    }
