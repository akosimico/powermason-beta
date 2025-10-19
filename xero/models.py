from django.db import models
from django.utils import timezone
from authentication.models import UserProfile

class XeroConnection(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True)
    expires_at = models.DateTimeField()
    tenant_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def is_valid(self):
        """Check if the connection is still valid (not expired)"""
        return timezone.now() < self.expires_at
    
    def __str__(self):
        return f"Xero connection for {self.user.full_name or self.user.user.email}"
