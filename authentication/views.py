from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
import os

# ... existing code ...

@login_required
def debug_email_config(request):
    """
    Debug email configuration - only for superusers
    """
    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            # Get test email from form
            test_email = request.POST.get('test_email', request.user.email)
            
            # Send test email
            send_mail(
                subject='Test Email from Powermason',
                message='This is a test email to verify email configuration.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[test_email],
                fail_silently=False,
            )
            
            messages.success(request, f'✅ Test email sent successfully to {test_email}!')
            
        except Exception as e:
            messages.error(request, f'❌ Failed to send test email: {str(e)}')
    
    # Email configuration info
    email_config = {
        'backend': settings.EMAIL_BACKEND,
        'host': getattr(settings, 'EMAIL_HOST', 'Not set'),
        'port': getattr(settings, 'EMAIL_PORT', 'Not set'),
        'user': getattr(settings, 'EMAIL_HOST_USER', 'Not set'),
        'password_set': bool(getattr(settings, 'EMAIL_HOST_PASSWORD', None)),
        'use_tls': getattr(settings, 'EMAIL_USE_TLS', 'Not set'),
        'use_ssl': getattr(settings, 'EMAIL_USE_SSL', 'Not set'),
        'timeout': getattr(settings, 'EMAIL_TIMEOUT', 'Not set'),
        'from_email': settings.DEFAULT_FROM_EMAIL,
    }
    
    # Environment info
    env_info = {
        'environment': os.getenv('ENVIRONMENT', 'Not set'),
        'render': os.getenv('RENDER', 'Not set'),
        'debug': settings.DEBUG,
        'email_address_set': bool(os.getenv('EMAIL_ADDRESS')),
        'email_password_set': bool(os.getenv('EMAIL_HOST_PASSWORD')),
        'postgres_locally': os.getenv('POSTGRES_LOCALLY', 'Not set'),
    }
    
    # All environment variables (for debugging)
    all_env_vars = {k: v for k, v in os.environ.items() if 'EMAIL' in k or 'ENVIRONMENT' in k or 'RENDER' in k}
    
    context = {
        'email_config': email_config,
        'env_info': env_info,
        'all_env_vars': all_env_vars,
    }
    
    return render(request, 'authentication/debug_email.html', context)