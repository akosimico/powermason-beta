import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.base import ContentFile

from scheduling.models import ProjectTask, ProgressUpdate, ProgressFile
from authentication.models import UserProfile
from notifications.models import Notification, NotificationStatus

from django.urls import reverse

User = get_user_model()


class Command(BaseCommand):
    help = "Generate fake progress updates for tasks (with notifications)."

    def handle(self, *args, **kwargs):
        tasks = ProjectTask.objects.all()[:20]  # Limit for testing
        pms = UserProfile.objects.filter(role="PM")
        oms = UserProfile.objects.filter(role="OM")
        egs = UserProfile.objects.filter(role="EG")

        if not pms.exists():
            self.stdout.write(self.style.ERROR("No PM users found! Cannot generate updates."))
            return

        total_updates = 0
        total_notifications = 0

        for task in tasks:
            pm = random.choice(pms)

            # Create progress update
            update = ProgressUpdate.objects.create(
                task=task,
                reported_by=pm,
                progress_percent=random.choice([10, 25, 40, 60, 80, 100]),
                remarks=f"Auto-generated update for {task.task_name}.",
                created_at=timezone.now(),
            )

            # --- Notify OMs + EGs ---
            om_eg_users = UserProfile.objects.filter(role__in=["OM", "EG"])
            notif_message = (
                f"{pm.full_name} submitted a progress report "
                f"for Project '{task.project.project_name}' (Task: {task.task_name})"
            )

            if om_eg_users.exists():
                notif = Notification.objects.create(
                    message=notif_message,
                    link=reverse("review_updates"),
                )
                for user in om_eg_users:
                    NotificationStatus.objects.create(notification=notif, user=user)
                    total_notifications += 1

            # --- Notify the PM themselves ---
            notif_pm = Notification.objects.create(
                message=(
                    f"You submitted a progress report for Project "
                    f"'{task.project.project_name}' (Task: {task.task_name})"
                ),
                link=reverse(
                    "task_list",
                    kwargs={
                        "project_id": task.project.id,
                        "token": "demo-token",
                        "role": pm.role,
                    },
                ),
            )
            NotificationStatus.objects.create(notification=notif_pm, user=pm)
            total_notifications += 1

            total_updates += 1
            self.stdout.write(self.style.SUCCESS(
                f"📊 Progress update {update.progress_percent}% submitted for "
                f"{task.project.project_name} - {task.task_name}"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Done! Generated {total_updates} progress updates with {total_notifications} notifications."
        ))