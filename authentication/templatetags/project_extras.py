from django import template
from datetime import datetime
from authentication.models import UserProfile

register = template.Library()

PROJECT_TYPE_MAP = {
    "IND": "Industrial",
    "RES": "Residential",
    "COM": "Commercial",
}

PROJECT_CATEGORY_MAP = {
    "PRI": "Private",
    "PUB": "Public",
    "REN": "Renovation",
    "NEW": "New Build",
}

PROJECT_SOURCE_MAP = {
    "GC": "General Contractor",
    "DC": "Direct Client",
}

@register.filter
def display_type(value):
    return PROJECT_TYPE_MAP.get(value, value or "N/A")

@register.filter
def display_category(value):
    return PROJECT_CATEGORY_MAP.get(value, value or "N/A")

@register.filter
def display_source(value):
    return PROJECT_SOURCE_MAP.get(value, value or "N/A")

@register.filter
def get_project_type_name(project_type_id):
    """Get the project type name from ID stored in project data"""
    if not project_type_id:
        return "N/A"

    try:
        from project_profiling.models import ProjectType
        project_type = ProjectType.objects.get(id=int(project_type_id))
        return project_type.name
    except (ProjectType.DoesNotExist, ValueError, TypeError):
        return str(project_type_id) or "N/A"

@register.filter
def get_item(dictionary, key):
    """Access dict items safely in templates."""
    if dictionary and isinstance(dictionary, dict):
        return dictionary.get(key, None)
    return None

@register.filter
def format_date(value):
    """Format string/DateField to 'M d, Y' or return N/A"""
    if not value:
        return "N/A"
    try:
        if isinstance(value, str):
            value = datetime.strptime(value, "%Y-%m-%d")
        return value.strftime("%b %d, %Y")
    except Exception:
        return "N/A"

@register.filter
def get_user_full_name(user_id):
    """Return full name for a given UserProfile id."""
    try:
        user = UserProfile.objects.get(id=user_id)
        return user.full_name
    except UserProfile.DoesNotExist:
        return "N/A"
