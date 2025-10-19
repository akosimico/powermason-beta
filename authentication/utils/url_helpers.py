"""
URL helper utilities for session-based URLs.
Simplified to remove token-based logic.
"""

from django.urls import reverse
from django.contrib.auth import get_user_model
from ..models import UserProfile

User = get_user_model()


def get_user_role(request):
    """
    Get the user's role from their profile.
    Returns None if user is not authenticated or has no profile.
    """
    if not request.user.is_authenticated:
        return None
    
    try:
        profile = UserProfile.objects.get(user=request.user)
        return profile.role
    except UserProfile.DoesNotExist:
        return None


def get_dashboard_url(request):
    """
    Get the dashboard URL for the current user.
    """
    return reverse('dashboard')


def get_project_list_url(request):
    """
    Get the project list URL for the current user.
    """
    return reverse('project_list')


def get_project_view_url(request, project_source, project_id):
    """
    Get the project view URL for the current user.
    """
    return reverse('project_view', kwargs={'project_source': project_source, 'pk': project_id})


def get_task_list_url(request, project_id):
    """
    Get the task list URL for the current user.
    """
    return reverse('task_list', kwargs={'project_id': project_id})


def get_gantt_view_url(request, project_id):
    """
    Get the Gantt view URL for the current user.
    """
    return reverse('task_gantt_view', kwargs={'project_id': project_id})