from django.db import models
from authentication.models import UserProfile

PROJECT_SOURCES = [
        ("GC", "General Contractor"),
        ("DC", "Direct Client"),
    ]

class Client(models.Model):
    # Basic company information
    company_name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Address information
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    
    # Business information
    client_type = models.CharField(
        max_length=20, 
        choices=PROJECT_SOURCES,
        default='DC',
        help_text="Type of client - Direct or General Contractor"
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    project_types = models.ManyToManyField("project_profiling.ProjectType", blank=True, related_name='clients')
    
    contract = models.FileField(
        upload_to='contracts/',
        blank=True,
        null=True,
        help_text="Upload client contract (PDF, DOC, DOCX)"
    )
    
    
    # Audit fields
    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    xero_contact_id = models.CharField(max_length=100, null=True, blank=True)
    xero_last_sync = models.DateTimeField(null=True, blank=True)
    
    def sync_to_xero(self, request):
        """Convenience method to sync this client to Xero"""
        from xero.xero_sync import sync_client_to_xero
        return sync_client_to_xero(request, self)
    
    class Meta:
        ordering = ['company_name', 'contact_name']
        unique_together = ['company_name']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
    
    def __str__(self):
        return f"{self.company_name} ({self.contact_name}) - {self.get_client_type_display()}"
    
    def get_full_address(self):
        parts = [self.address, self.city, self.state, self.zip_code]
        return ', '.join([part for part in parts if part.strip()])

    @property
    def is_synced_to_xero(self):
        """Check if client is synced to Xero"""
        return bool(self.xero_contact_id)
    
    @property 
    def xero_contact_url(self):
        """Get the Xero contact URL if synced"""
        if self.xero_contact_id:
            return f"https://go.xero.com/Contacts/View/{self.xero_contact_id}"
        return None
    
    def get_project_count(self):
        return self.projects.count()
    
    def is_contractor(self):
        return self.client_type == 'GC'
    
    def is_direct_client(self):
        return self.client_type == 'DC'