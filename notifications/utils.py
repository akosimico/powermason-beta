from notifications.models import Notification

def send_notification(user=None, roles=None, message=None, link=None):
    """
    Sends notifications to a specific user and/or roles with a preformatted message.
    """
    if user and message:
        Notification.objects.create(user=user, message=message, link=link)

    if roles and message:
        for role in roles:
            Notification.objects.create(role=role, message=message, link=link)
