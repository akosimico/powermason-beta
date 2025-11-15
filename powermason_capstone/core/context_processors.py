from django.conf import settings

def app_version(request):
    return {
        'APP_VERSION': getattr(settings, 'APP_VERSION', 'v1.2.0-alpha')
    }
