from django import template

register = template.Library()

@register.filter
def has_role(user, role_codes):
    """
    Checks if user.userprofile.role matches any in a comma-separated list.
    Usage:
    {% if user|has_role:"OM,EG" %}
    """
    if not hasattr(user, "userprofile"):
        return False
    allowed_roles = [r.strip() for r in role_codes.split(",")]
    return user.userprofile.role in allowed_roles
