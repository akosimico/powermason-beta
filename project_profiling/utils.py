from django.db.models import Sum, F

def recalc_project_progress(project):
    tasks = project.tasks.all()

    if not tasks.exists():
        project.progress = 0
        project.is_completed = False
        project.status = "PL"
        project.save(update_fields=["progress", "status", "is_completed"])
        return

    # Weighted progress
    total_weight = tasks.aggregate(total=Sum("weight"))["total"] or 0
    weighted_progress = 0

    for task in tasks:
        if total_weight > 0:
            weighted_progress += (task.progress * task.weight) / total_weight
        else:
            weighted_progress += task.progress / tasks.count()

    project.progress = round(weighted_progress, 2)

    # ✅ Auto-update project status
    if project.progress >= 100:
        project.status = "CP"  # Completed
        project.is_completed = True
    elif project.progress > 0:
        project.status = "OG"  # Ongoing
        project.is_completed = False
    else:
        project.status = "PL"  # Planned
        project.is_completed = False

    project.save(update_fields=["progress", "status", "is_completed"])
