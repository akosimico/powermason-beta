from notifications.models import Notification, NotificationStatus
from authentication.models import UserProfile

def send_notification(user=None, roles=None, message=None, link=None):
    """
    Sends notifications to a specific user and/or roles with a preformatted message.
    Creates NotificationStatus entries to link notifications to users.
    """
    if user and message:
        # Create notification for specific user
        notification = Notification.objects.create(message=message, link=link)
        NotificationStatus.objects.create(
            notification=notification,
            user=user,
            is_read=False,
            cleared=False
        )

    if roles and message:
        for role in roles:
            # Create notification with role
            notification = Notification.objects.create(role=role, message=message, link=link)

            # Get all users with this role and create NotificationStatus for each
            users_with_role = UserProfile.objects.filter(role=role)
            for user_profile in users_with_role:
                NotificationStatus.objects.create(
                    notification=notification,
                    user=user_profile,
                    is_read=False,
                    cleared=False
                )
