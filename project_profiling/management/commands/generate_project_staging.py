# management/commands/generate_project_staging.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
import random

from authentication.models import UserProfile
from project_profiling.models import ProjectStaging, ProjectStagingHistory


class Command(BaseCommand):
    help = "Generate dummy ProjectStaging and ProjectStagingHistory records for testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Number of project staging records to generate",
        )

    def handle(self, *args, **options):
        fake = Faker()
        count = options["count"]

        users = list(UserProfile.objects.all())
        if not users:
            self.stdout.write(self.style.ERROR("❌ No UserProfiles found. Please create some first."))
            return

        sources = ["GC", "DC"]
        statuses = ["PL", "AP", "RJ"]

        for i in range(count):
            created_by = random.choice(users)

            project_data = {
                "project_name": fake.company() + " Project",
                "location": fake.city(),
                "duration": f"{random.randint(3, 24)} months",
                "budget": round(random.uniform(50000, 5000000), 2),
                "description": fake.text(max_nb_chars=200),
            }

            staging = ProjectStaging.objects.create(
                created_by=created_by,
                project_data=project_data,
                project_source=random.choice(sources),
                project_id_placeholder=f"TMP-{fake.unique.random_int(1000, 9999)}",
                status=random.choice(statuses),
                submitted_at=timezone.now(),
            )

            # Optionally add some history logs
            for _ in range(random.randint(1, 3)):
                ProjectStagingHistory.objects.create(
                    project_staging=staging,
                    created_by=random.choice(users),
                    status=random.choice(statuses),
                    comments=fake.sentence(),
                    submitted_at=timezone.now(),
                )

        self.stdout.write(self.style.SUCCESS(f"✅ Successfully created {count} ProjectStaging records with history"))
