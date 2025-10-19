from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta, date

from django.contrib.auth import get_user_model
from project_profiling.models import ProjectProfile, ProjectBudget, FundAllocation, ProjectCost, CostCategory
from scheduling.models import ProjectTask
from authentication.models import UserProfile

User = get_user_model()

class Command(BaseCommand):
    help = "Create 10 dummy projects with tasks, budgets, allocations, and costs"

    def handle(self, *args, **kwargs):
        # --- Create dummy users if not exist ---
        roles_needed = ['PM', 'OM', 'EG']
        dummy_users = {}
        for role in roles_needed:
            profile = UserProfile.objects.filter(role=role).first()
            if not profile:
                user = User.objects.create_user(
    email=f'dummy_{role.lower()}@example.com',
    password='password123'
)
                profile = UserProfile.objects.create(user=user, role=role, full_name=f'Dummy {role}')
                self.stdout.write(f"Created dummy user for role {role}")
            dummy_users[role] = profile

        self.stdout.write("\nCreating 10 dummy projects...\n")

        categories = [c[0] for c in CostCategory.choices]  # LAB, MAT, EQP, SUB, OTH

        for i in range(1, 11):
            project_name = f"Dummy Project {i}"
            start = date.today() - timedelta(days=random.randint(0, 30))
            end = start + timedelta(days=random.randint(30, 120))
            status = random.choice(["PL", "OG", "CP", "CN"])

            project = ProjectProfile.objects.create(
                project_name=project_name,
                project_manager=dummy_users['PM'],
                created_by=dummy_users['OM'],
                assigned_to=dummy_users['EG'],
                start_date=start,
                target_completion_date=end,
                status=status,
                project_source=random.choice(["GC", "DC"]),
                project_type=random.choice(["RES", "COM", "IND", "OTH"]),
                project_category=random.choice(["PUB", "PRI", "REN", "NEW"]),
                location=f"Dummy Location {i}",
                estimated_cost=Decimal(random.randint(10000, 100000)),
                approved_budget=Decimal(random.randint(50000, 150000)),
            )
            self.stdout.write(f"Created project: {project_name}")

            # --- Create tasks ---
            for t in range(random.randint(3, 5)):
                task_start = start + timedelta(days=random.randint(0, 10))
                task_end = task_start + timedelta(days=random.randint(5, 20))
                progress = random.uniform(0, 100)

                ProjectTask.objects.create(
                    project=project,
                    task_name=f"Task {t+1} for {project_name}",
                    start_date=task_start,
                    end_date=task_end,
                    progress=round(progress, 2),
                    weight=random.randint(1, 5),
                    assigned_to=dummy_users['EG'],
                )

            # --- Create budgets, allocations, and costs ---
            for cat in categories:
                planned_amount = Decimal(random.randint(5000, 50000))
                budget = ProjectBudget.objects.create(
                    project=project,
                    category=cat,
                    planned_amount=planned_amount
                )

                FundAllocation.objects.create(
                    project_budget=budget,
                    amount=planned_amount * Decimal(random.uniform(0.5, 1.0))
                )

                ProjectCost.objects.create(
                    project=project,
                    category=cat,
                    amount=planned_amount * Decimal(random.uniform(0.3, 0.9))
                )

        self.stdout.write(self.style.SUCCESS("\n✅ 10 Dummy Projects Created Successfully!"))
