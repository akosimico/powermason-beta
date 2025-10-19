from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from project_profiling.models import ProjectProfile
from scheduling.models import ProjectTask
from authentication.utils.tokens import get_user_profile, verify_user_profile
from authentication.utils.decorators import verified_email_required, role_required
from manage_client.models import Client

@login_required
@verified_email_required
def progress_monitoring(request):
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")
    
    print('pumapasok')
    user_role = verified_profile.role
    
    # Get filter parameters
    show_archived = request.GET.get("show_archived") == "1"
    show_completed = request.GET.get("show_completed") == "1"
    status_filter = request.GET.get("status", "")
    search_query = request.GET.get("search", "").strip()
    
    # Fetch projects based on role
    # --- Fetch projects by role ---
    if user_role == "PM":
        projects = ProjectProfile.objects.filter(project_manager=verified_profile)
    elif user_role == "VO":
        try:
            user_email = verified_profile.user.email
            if user_email:
                matching_clients = Client.objects.filter(email=user_email)
                if matching_clients.exists():
                    projects = ProjectProfile.objects.filter(client__in=matching_clients)
        except Client.DoesNotExist:
            pass
    else:
        projects = ProjectProfile.objects.all()
    # Filter by archived status
    if show_archived:
        projects = projects.filter(archived=True)   # only archived
    else:
        projects = projects.filter(archived=False)  # only active
        
        # Hide completed and cancelled projects by default (only for active projects)
        if not show_completed:
            projects = projects.exclude(status__in=['CP', 'CN'])
    
    # Search filter
    if search_query:
        projects = projects.filter(project_name__icontains=search_query)
            
    # Filter by specific status if provided
    if status_filter:
        projects = projects.filter(status=status_filter)

    # Order projects by status priority and name
    status_order = ['OG', 'PL', 'CP', 'CN']  # Ongoing, Planned, Completed, Cancelled
    projects = projects.extra(
        select={'status_order': f"CASE status {' '.join([f'WHEN \'{status}\' THEN {i}' for i, status in enumerate(status_order)])} ELSE 999 END"}
    ).order_by('status_order', 'project_name')

    # Prepare project data
    project_data = []
    status_counts = {'total': 0, 'ongoing': 0, 'completed': 0, 'planned': 0, 'cancelled': 0}
    
    # Check if projects exist
    if not projects.exists():
        # Handle case when no projects are found
        project_data = []
        status_counts = {'total': 0, 'ongoing': 0, 'completed': 0, 'planned': 0, 'cancelled': 0}
    else:
        for project in projects:
            tasks = ProjectTask.objects.filter(project=project).order_by("start_date")
            task_progress = [
                (
                    task.task_name,
                    round(task.progress or 0, 2),
                    task.weight or 1,
                    task.id
                )
                for task in tasks
            ]
            
            # Calculate total progress
            total_weight = sum(task.weight or 1 for task in tasks) or 1
            total_progress = sum((task.progress or 0) * (task.weight or 1) for task in tasks) / total_weight

            project_data.append({
                "project_name": project.project_name,
                "project_status": project.status,
                "task_progress": task_progress,
                "total_progress": round(total_progress, 2),
                "archived": project.archived,
                "project_id": project.id,
                "project_source": project.project_source,
            })
            
            # Count projects by status
            status_counts['total'] += 1
            if project.status == 'OG':
                status_counts['ongoing'] += 1
            elif project.status == 'CP':
                status_counts['completed'] += 1
            elif project.status == 'PL':
                status_counts['planned'] += 1
            elif project.status == 'CN':
                status_counts['cancelled'] += 1

    # Get all available statuses for filter dropdown
    all_statuses = [
        ('OG', 'Ongoing'),
        ('PL', 'Planned'), 
        ('CP', 'Completed'),
        ('CN', 'Cancelled')
    ]

    context = {
        "projects": project_data,
        "show_archived": show_archived,
        "show_completed": show_completed,
        "status_filter": status_filter,
        "status_counts": status_counts,
        "all_statuses": all_statuses,
        "user_role": user_role,
        "has_projects": len(project_data) > 0,
    }
    return render(request, "progress/dashboard_projects_list.html", context)