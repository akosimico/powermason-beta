from django.templatetags.static import static
from scheduling.models import ProgressUpdate
from authentication.models import UserProfile

def user_context(request):
    """
    Provides avatar, pending updates, and role globally.
    """
    user = request.user
    context = {
        'avatar_url': static('img/default-avatar.jpg'),
        'pending_count': 0,
        'role': None,
    }

    if user.is_authenticated:
        # Avatar
        social = user.socialaccount_set.first()
        context['avatar_url'] = social.get_avatar_url() if social else context['avatar_url']

        # Role
        role = getattr(user, 'role', None)
        context['role'] = role

        # Pending count (OM, EG, or superuser)
        if role in ['OM', 'EG'] or user.is_superuser:
            context['pending_count'] = ProgressUpdate.objects.filter(status='P').count()

    return context
