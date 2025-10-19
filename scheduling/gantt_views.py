# ========================================
# GANTT CHART & SCHEDULE VISUALIZATION
# Interactive timeline view for project tasks
# ========================================

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Min, Max, Q
from datetime import datetime, timedelta
from decimal import Decimal

from authentication.utils.decorators import verified_email_required, role_required
from authentication.utils.tokens import get_user_profile, verify_user_profile
from .models import ProjectTask, ProjectScope
from project_profiling.models import ProjectProfile


@login_required
@verified_email_required
@role_required('EG', 'OM', 'PM')
def task_gantt_view(request, project_id):
    """
    Gantt chart visualization for project tasks
    Shows tasks on timeline with dependencies
    """
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    project = get_object_or_404(ProjectProfile, id=project_id)

    # Check permissions - PM can only see their projects
    if verified_profile.role == 'PM' and project.project_manager != verified_profile:
        return render(request, 'errors/403.html', status=403)

    # Get all active tasks
    tasks = ProjectTask.objects.filter(
        project=project,
        is_archived=False
    ).select_related('scope', 'assigned_to__user').prefetch_related('dependencies').order_by('start_date')

    # Calculate project timeline
    if tasks.exists():
        project_start = tasks.aggregate(Min('start_date'))['start_date__min']
        project_end = tasks.aggregate(Max('end_date'))['end_date__max']

        if project_start and project_end:
            project_duration = (project_end - project_start).days + 1
        else:
            project_duration = 0
    else:
        project_start = None
        project_end = None
        project_duration = 0

    # Group tasks by scope
    scopes = ProjectScope.objects.filter(
        project=project,
        is_deleted=False,
        tasks__is_archived=False
    ).distinct().prefetch_related('tasks')

    # Calculate statistics
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='CP').count()
    ongoing_tasks = tasks.filter(status='OG').count()
    planned_tasks = tasks.filter(status='PL').count()

    # Find critical path (simplified - tasks with no slack)
    # In a real implementation, you'd use CPM algorithm
    critical_tasks = []
    for task in tasks:
        # Check if task has dependencies
        if task.dependencies.exists():
            # Check if start_date matches dependency end_date
            latest_dep_end = task.dependencies.aggregate(Max('end_date'))['end_date__max']
            if latest_dep_end and task.start_date == latest_dep_end + timedelta(days=1):
                critical_tasks.append(task.id)

    context = {
        'token': token,
        'role': role,
        'project': project,
        'tasks': tasks,
        'scopes': scopes,
        'project_start': project_start,
        'project_end': project_end,
        'project_duration': project_duration,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'ongoing_tasks': ongoing_tasks,
        'planned_tasks': planned_tasks,
        'critical_tasks': critical_tasks,
    }

    return render(request, 'scheduling/task_gantt_view.html', context)


@login_required
@verified_email_required
@require_http_methods(["GET"])
def api_gantt_data(request, project_id):
    """
    API endpoint to get Gantt chart data in JSON format
    Compatible with Frappe Gantt and other libraries
    """
    try:
        project = get_object_or_404(ProjectProfile, id=project_id)

        # Check permissions
        user_profile = request.user.userprofile
        if user_profile.role == 'PM' and project.project_manager != user_profile:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        tasks = ProjectTask.objects.filter(
            project=project,
            is_archived=False
        ).select_related('scope', 'assigned_to__user').prefetch_related('dependencies').order_by('start_date')

        gantt_data = []
        for task in tasks:
            # Convert to Frappe Gantt format
            task_data = {
                'id': str(task.id),
                'name': task.task_name,
                'start': task.start_date.strftime('%Y-%m-%d'),
                'end': task.end_date.strftime('%Y-%m-%d'),
                'progress': float(task.progress),
                'dependencies': ','.join([str(dep.id) for dep in task.dependencies.all()]),
                'custom_class': f'status-{task.status}',

                # Additional metadata
                'scope': task.scope.name if task.scope else '',
                'assigned_to': task.assigned_to.full_name if task.assigned_to else '',
                'weight': float(task.weight),
                'status': task.status,
                'status_display': task.get_status_display(),
                'duration': float(task.duration_days) if task.duration_days else 0,
                'manhours': float(task.manhours) if task.manhours else 0,
            }
            gantt_data.append(task_data)

        return JsonResponse({
            'success': True,
            'tasks': gantt_data,
            'project_name': project.project_name,
            'project_code': project.project_id,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@verified_email_required
@role_required('EG', 'OM')
def api_update_task_dates(request, task_id):
    """
    API to update task dates (for drag-and-drop rescheduling)
    """
    import json

    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        task = get_object_or_404(ProjectTask, id=task_id)
        data = json.loads(request.body)

        new_start = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        new_end = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()

        task.start_date = new_start
        task.end_date = new_end
        task.save()

        return JsonResponse({
            'success': True,
            'message': 'Task dates updated successfully'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@verified_email_required
@role_required('EG', 'OM', 'PM')
def three_week_lookahead(request, project_id):
    """
    Three-week look-ahead schedule
    Shows tasks coming up in the next 3 weeks
    """
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    project = get_object_or_404(ProjectProfile, id=project_id)

    # Check permissions
    if verified_profile.role == 'PM' and project.project_manager != verified_profile:
        return render(request, 'errors/403.html', status=403)

    today = datetime.now().date()
    week_1_end = today + timedelta(days=7)
    week_2_end = today + timedelta(days=14)
    week_3_end = today + timedelta(days=21)

    # Get tasks for each week
    week_1_tasks = ProjectTask.objects.filter(
        project=project,
        is_archived=False,
        start_date__lte=week_1_end,
        end_date__gte=today
    ).select_related('scope', 'assigned_to__user').order_by('start_date')

    week_2_tasks = ProjectTask.objects.filter(
        project=project,
        is_archived=False,
        start_date__lte=week_2_end,
        start_date__gt=week_1_end
    ).select_related('scope', 'assigned_to__user').order_by('start_date')

    week_3_tasks = ProjectTask.objects.filter(
        project=project,
        is_archived=False,
        start_date__lte=week_3_end,
        start_date__gt=week_2_end
    ).select_related('scope', 'assigned_to__user').order_by('start_date')

    context = {
        'token': token,
        'role': role,
        'project': project,
        'today': today,
        'week_1_start': today,
        'week_1_end': week_1_end,
        'week_2_start': week_1_end + timedelta(days=1),
        'week_2_end': week_2_end,
        'week_3_start': week_2_end + timedelta(days=1),
        'week_3_end': week_3_end,
        'week_1_tasks': week_1_tasks,
        'week_2_tasks': week_2_tasks,
        'week_3_tasks': week_3_tasks,
    }

    return render(request, 'scheduling/three_week_lookahead.html', context)
