import random
from datetime import date, timedelta, datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from authentication.models import UserProfile
from project_profiling.models import ProjectStaging


def serialize_field(value):
    """Convert unserializable types to string/URL for JSON storage."""
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, 'full_name'):  # UserProfile
        return value.full_name
    if hasattr(value, 'name') and not hasattr(value, 'read'):  # e.g. ChoiceField
        return str(value.name)
    if hasattr(value, 'url'):  # FileField / ImageField
        return value.url
    if hasattr(value, 'read'):  # UploadedFile
        return value.name
    return value


class Command(BaseCommand):
    help = "Create dummy ProjectStaging entries for testing review projects"

    def handle(self, *args, **kwargs):
        # Ensure at least one user exists
        user, _ = User.objects.get_or_create(username="admin", defaults={"email": "admin@example.com"})
        user_profile, _ = UserProfile.objects.get_or_create(user=user, defaults={"role": "PM"})

        sources = ["GC", "DC"]
        types = ["RES", "COM", "IND", "OTH"]
        categories = ["PUB", "PRI", "REN", "NEW"]
    
        for i in range(5):
            # Fake form-like cleaned_data dict
            pm_user = UserProfile.objects.filter(role="PM").order_by("?").first()

            project_data = {
            "project_name": f"Staging Project {i+1}",
            "project_source": random.choice(sources),
            "project_type": random.choice(types),
            "project_category": random.choice(categories),
            "description": "This is a staging project for testing review workflow.",
            "gc_company_name": "ABC Builders",
            "gc_license_number": f"LIC-{1000+i}",
            "gc_contact_person": "John Doe",
            "gc_contact_number": "09171234567",
            "gc_contact_email": "gc@example.com",
            "client_name": "XYZ Corporation",
            "client_address": "123 Main St, Metro City",
            "client_contact_person": "Jane Smith",
            "client_contact_number": "09281234567",
            "client_contact_email": "client@example.com",
            "location": f"Site Location {i+1}",
            "gps_coordinates": "14.5995,120.9842",
            "city_province": "Metro Manila",
            "start_date": date.today(),
            "target_completion_date": date.today() + timedelta(days=90),
            "estimated_cost": Decimal("1000000.00") + i * 100000,
            "payment_terms": "50% upfront, 50% on completion",
            "site_engineer": "Engr. Michael Tan",
            "subcontractors": "Subcontractor A, Subcontractor B",
            "project_manager": pm_user.full_name if pm_user else "Unassigned",  # ✅ new field
            "status": "PL",
        }

            # Serialize data for JSONField
            serialized_data = {k: serialize_field(v) for k, v in project_data.items()}

            project = ProjectStaging.objects.create(
                created_by=user_profile,
                project_source=serialized_data["project_source"],
                project_data=serialized_data,
            )
            self.stdout.write(self.style.SUCCESS(f"Created staging project: {serialized_data['project_name']} ({project.id})"))
