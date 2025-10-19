# manage_client/templatetags/xero_tags.py
from django import template
from xero.models import XeroConnection

register = template.Library()

@register.simple_tag
def has_xero_connection(user):
    """Check if user has a valid Xero connection"""
    if not user.is_authenticated:
        return False
    
    try:
        xero_conn = XeroConnection.objects.get(user=user.userprofile)
        return xero_conn.is_valid()
    except (XeroConnection.DoesNotExist, AttributeError):
        return False

@register.filter
def xero_connected(user):
    """Filter to check if user has Xero connection"""
    if not user.is_authenticated:
        return False
    
    try:
        xero_conn = XeroConnection.objects.get(user=user.userprofile)
        return xero_conn.is_valid()
    except (XeroConnection.DoesNotExist, AttributeError):
        return False