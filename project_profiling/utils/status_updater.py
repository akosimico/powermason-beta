# project_profiling/utils/status_updater.py

def update_project_status(project, actual_progress, has_real_progress):
    """
    Automatically updates the project's status based on its current progress.
    """

    # ✅ Make sure the model actually has a 'status' field
    if not hasattr(project, "status"):
        return

    # Determine new status
    if actual_progress >= 100:
        new_status = "CP"  # Completed
    elif actual_progress > 0.01:
        new_status = "OG"  # Ongoing
    elif actual_progress == 0:
        new_status = "PL"  # Planned
    else:
        new_status = project.status  # keep unchanged if uncertain

    # ✅ Only update if status has changed
    if project.status != new_status:
        project.status = new_status
        project.save(update_fields=["status"])
