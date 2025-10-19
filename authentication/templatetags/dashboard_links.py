from django import template
from django.urls import reverse

register = template.Library()

@register.simple_tag
def dashboard_link(profile):
    # Session-based dashboard link
    return reverse("dashboard")
