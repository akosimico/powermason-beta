"""
Template tags for URL helpers for session-based URLs.
"""

from django import template
from django.urls import reverse
from authentication.utils.url_helpers import (
    get_user_role,
    get_dashboard_url, get_project_list_url, get_project_view_url,
    get_task_list_url, get_gantt_view_url
)

register = template.Library()


@register.simple_tag(takes_context=True)
def smart_reverse(context, url_name, *args, **kwargs):
    """
    Template tag to generate URLs using standard Django reverse.
    Usage: {% smart_reverse 'project_list' %}
    """
    return reverse(url_name, args=args, kwargs=kwargs)


@register.simple_tag(takes_context=True)
def dashboard_url(context):
    """
    Template tag to get the appropriate dashboard URL.
    Usage: {% dashboard_url %}
    """
    request = context['request']
    return get_dashboard_url(request)


@register.simple_tag(takes_context=True)
def project_list_url(context):
    """
    Template tag to get the appropriate project list URL.
    Usage: {% project_list_url %}
    """
    request = context['request']
    return get_project_list_url(request)


@register.simple_tag(takes_context=True)
def project_view_url(context, project_source, project_id):
    """
    Template tag to get the appropriate project view URL.
    Usage: {% project_view_url 'general' project.id %}
    """
    request = context['request']
    return get_project_view_url(request, project_source, project_id)


@register.simple_tag(takes_context=True)
def task_list_url(context, project_id):
    """
    Template tag to get the appropriate task list URL.
    Usage: {% task_list_url project.id %}
    """
    request = context['request']
    return get_task_list_url(request, project_id)


@register.simple_tag(takes_context=True)
def gantt_view_url(context, project_id):
    """
    Template tag to get the appropriate Gantt view URL.
    Usage: {% gantt_view_url project.id %}
    """
    request = context['request']
    return get_gantt_view_url(request, project_id)


# Removed user_token template tag as tokens are no longer used


@register.simple_tag(takes_context=True)
def user_role(context):
    """
    Template tag to get the current user's role.
    Usage: {% user_role %}
    """
    request = context['request']
    return get_user_role(request)
