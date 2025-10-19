import random
import re
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from faker import Faker

from authentication.models import UserProfile
from employees.models import Employee

fake = Faker()


class Command(BaseCommand):
    help = "Generate random, valid employee data for testing (safe length and format)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=20,
            help="Number of employees to generate (default: 20)",
        )

    def handle(self, *args, **options):
        count = options["count"]
        created = 0

        roles = [r[0] for r in Employee.EMPLOYEE_ROLE_CHOICES]
        departments = [
            "Engineering",
            "Procurement",
            "Safety",
            "Quality Assurance",
            "Field Operations",
            "Logistics",
            "Finance",
        ]

        # Get a user for created_by (optional)
        user_profile = UserProfile.objects.first()
        created_by = user_profile.user if user_profile else None

        if not created_by:
            self.stdout.write(self.style.WARNING("⚠ No UserProfile found — 'created_by' set to None."))

        for _ in range(count):
            role = random.choice(roles)
            first_name = fake.first_name()
            last_name = fake.last_name()

            # Employment details
            hire_date = fake.date_between(start_date="-3y", end_date="-1y")
            contract_duration = random.randint(180, 720)  # 6 to 24 months
            contract_end_date = hire_date + timedelta(days=contract_duration)
            status = random.choice(["active", "active", "inactive", "on_leave"])

            # Generate clean and safe values
            email = f"{first_name.lower()}.{last_name.lower()}@powermason.com"
            phone = fake.phone_number()

            # Ensure phone fits DB (max_length=30 recommended)
            phone = re.sub(r"[^\d+]", "", phone)  # keep only digits and '+'
            phone = phone[:30]  # trim to safe length

            # Ensure department names fit DB
            department = random.choice(departments)[:50]

            # Create and save employee
            employee = Employee(
                role=role,
                first_name=first_name[:50],
                last_name=last_name[:50],
                email=email[:100],
                phone=phone,
                hire_date=hire_date,
                contract_end_date=contract_end_date,
                department=department,
                status=status,
                created_by=created_by,
            )

            employee.save()
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f"✅ Successfully generated {created} employee(s).")
        )
