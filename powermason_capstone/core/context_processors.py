from django.conf import settings

def app_version(request):
    return {
        'APP_VERSION': getattr(settings, 'APP_VERSION', 'v2.0.0')
    }
