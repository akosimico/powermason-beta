# notifications/models.py
from django.db import models
from django.utils import timezone
from authentication.models import UserProfile

class Notification(models.Model):
    ROLE_CHOICES = [
        ('VO', 'View Only'),
        ('PM', 'Project Manager'),
        ('OM', 'Operations Manager'),
        ('EG', 'Engineer'),
    ]

    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=2, choices=ROLE_CHOICES, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    archived = models.BooleanField(default=False)

    # Users who see this notification and their status
    users = models.ManyToManyField(UserProfile, through='NotificationStatus', related_name="notifications")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.message[:30]}"


class NotificationStatus(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    cleared = models.BooleanField(default=False)

    class Meta:
        unique_together = ("notification", "user")
