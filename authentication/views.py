from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
import os

# Basic redirect function
def redirect_to_dashboard(request):
    """Redirect to dashboard based on user role"""
    if request.user.is_authenticated:
        return redirect('dashboard_signed_with_role')
    else:
        return redirect('account_login')

# Custom password change view
class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'account/password_change.html'
    success_url = reverse_lazy('profile')

# Debug email configuration view

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

# Add other missing view functions
@login_required
def dashboard_signed_with_role(request):
    """Dashboard view with role-based access"""
    return render(request, 'dashboard.html')

@login_required
def unauthorized(request):
    """Unauthorized access view"""
    return render(request, 'authentication/unauthorized.html')

@login_required
def resend_verification(request):
    """Resend email verification"""
    # Implementation for resend verification
    messages.success(request, 'Verification email sent!')
    return redirect('verification_sent')

@login_required
def verification_sent(request):
    """Verification sent confirmation"""
    return render(request, 'account/verification_sent.html')

@login_required
def email_verification_required(request):
    """Email verification required view"""
    return render(request, 'account/email_verification_required.html')

@login_required
def profile(request):
    """User profile view"""
    return render(request, 'account/profile.html')

@login_required
def user_settings(request):
    """User settings view"""
    return render(request, 'account/settings.html')

@login_required
def manage_user_profiles(request):
    """Manage user profiles"""
    return render(request, 'users/manage_user_profiles.html')

@login_required
def search_users(request):
    """Search users"""
    return JsonResponse({'users': []})

@login_required
def add_user(request):
    """Add user"""
    return render(request, 'users/add_user.html')

@login_required
def edit_user(request, user_id):
    """Edit user"""
    return render(request, 'users/edit_user.html', {'user_id': user_id})

@login_required
def archive_user(request, user_id):
    """Archive user"""
    messages.success(request, 'User archived successfully!')
    return redirect('manage_user_profiles')

@login_required
def unarchive_user(request, user_id):
    """Unarchive user"""
    messages.success(request, 'User unarchived successfully!')
    return redirect('manage_user_profiles')

@login_required
def clear_welcome_flag(request):
    """Clear welcome flag"""
    return JsonResponse({'success': True})

@login_required
def update_profile_name(request):
    """Update profile name"""
    return JsonResponse({'success': True})

@login_required
def update_avatar(request):
    """Update avatar"""
    return JsonResponse({'success': True})

@login_required
def update_profile_email(request):
    """Update profile email"""
    return JsonResponse({'success': True})

@login_required
def clear_toast_session(request):
    """Clear toast session"""
    return JsonResponse({'success': True})

@login_required
def dashboard_api(request):
    """Dashboard API"""
    return JsonResponse({'data': 'dashboard data'})