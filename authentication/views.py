# Standard library
import json
from decimal import Decimal
from datetime import date
from django.contrib import messages as django_messages
from django.db.models import Value
from django.db import models
from django.db.models.functions import Concat

# Django imports
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.signing import BadSignature, SignatureExpired
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import PasswordChangeView
from django.db.models import Q, Sum, DecimalField
from django.db.models.functions import Coalesce
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# Allauth imports - FIXED IMPORTS
from allauth.account.models import EmailAddress, EmailConfirmation
from allauth.account.signals import email_confirmation_sent
from allauth.account.adapter import get_adapter
from django.contrib.sites.shortcuts import get_current_site
from allauth.account.views import ConfirmEmailView

# Authentication utils & decorators
from authentication.utils.tokens import (
    get_user_profile,
    verify_user_profile,
)
from authentication.utils.decorators import verified_email_required, role_required
import os
from django.core.mail import send_mail
from django.conf import settings
# Local app imports
from .models import UserProfile
from .forms import StyledPasswordChangeForm
from scheduling.models import ProgressUpdate
from scheduling.forms import ProjectTask
from project_profiling.models import ProjectProfile, ProjectBudget, ProjectCost, FundAllocation
from authentication.models import CustomUser
from manage_client.models import Client

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

@login_required
def debug_email_config(request):
    """
    Debug email configuration - only for superusers
    """
    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    # Initialize debug log
    debug_log = []
    error_details = None

    if request.method == 'POST':
        import socket
        import smtplib
        import traceback
        from time import time
        from django.core.mail import get_connection

        start_time = time()
        test_email = request.POST.get('test_email', request.user.email)

        debug_log.append(f"[{time():.2f}] Starting email test to: {test_email}")
        debug_log.append(f"[{time():.2f}] Using backend: {settings.EMAIL_BACKEND}")
        debug_log.append(f"[{time():.2f}] SMTP Host: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
        debug_log.append(f"[{time():.2f}] SMTP Port: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
        debug_log.append(f"[{time():.2f}] Email Timeout: {getattr(settings, 'EMAIL_TIMEOUT', 'Not set')} seconds")
        debug_log.append(f"[{time():.2f}] Connection Timeout: {getattr(settings, 'EMAIL_CONNECTION_TIMEOUT', 'Not set')} seconds")

        try:
            debug_log.append(f"[{time():.2f}] Opening SMTP connection...")

            # Test connection first
            connection = get_connection(fail_silently=False)
            debug_log.append(f"[{time():.2f}] Connection object created")

            connection.open()
            debug_log.append(f"[{time():.2f}] Connection opened successfully")

            # Send test email
            debug_log.append(f"[{time():.2f}] Sending email...")
            send_mail(
                subject='Test Email from Powermason',
                message='This is a test email to verify email configuration.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[test_email],
                fail_silently=False,
                connection=connection,
            )

            connection.close()
            debug_log.append(f"[{time():.2f}] Connection closed")

            elapsed_time = time() - start_time
            debug_log.append(f"[{time():.2f}] Email sent successfully in {elapsed_time:.2f} seconds")
            messages.success(request, f'Test email sent successfully to {test_email} in {elapsed_time:.2f} seconds!')

        except socket.timeout as e:
            elapsed_time = time() - start_time
            error_details = {
                'type': 'Socket Timeout',
                'message': f'Connection timed out after {elapsed_time:.1f} seconds',
                'details': str(e),
                'traceback': traceback.format_exc(),
                'suggestions': [
                    'Your EMAIL_TIMEOUT is set to 5 seconds but connection is taking longer',
                    'Check if smtp.sendgrid.net:587 is accessible from Render',
                    'Verify SendGrid API key is correct',
                    'Try increasing EMAIL_TIMEOUT to 10 seconds temporarily for testing',
                ]
            }
            debug_log.append(f"[{elapsed_time:.2f}] ERROR: Socket timeout")
            messages.error(request, f'Email timeout after {elapsed_time:.1f}s')

        except smtplib.SMTPAuthenticationError as e:
            elapsed_time = time() - start_time
            error_details = {
                'type': 'SMTP Authentication Error',
                'message': 'Failed to authenticate with SMTP server',
                'details': str(e),
                'traceback': traceback.format_exc(),
                'suggestions': [
                    'Check that SENDGRID_API_KEY environment variable is set correctly',
                    'API key should start with "SG." and be around 69 characters',
                    'Verify the API key has "Mail Send" permissions in SendGrid',
                    'Check if EMAIL_HOST_USER is set to "apikey" (not your email)',
                ]
            }
            debug_log.append(f"[{elapsed_time:.2f}] ERROR: Authentication failed")
            messages.error(request, 'SMTP Authentication failed')

        except smtplib.SMTPSenderRefused as e:
            elapsed_time = time() - start_time
            error_details = {
                'type': 'SMTP Sender Refused',
                'message': 'Sender email address was rejected',
                'details': str(e),
                'traceback': traceback.format_exc(),
                'suggestions': [
                    'Verify sender email in SendGrid Dashboard',
                    'Go to: Settings -> Sender Authentication -> Verify a Single Sender',
                    'Check your email inbox for SendGrid verification email',
                    f'Current FROM email: {settings.DEFAULT_FROM_EMAIL}',
                ]
            }
            debug_log.append(f"[{elapsed_time:.2f}] ERROR: Sender refused")
            messages.error(request, 'Sender email rejected')

        except smtplib.SMTPRecipientsRefused as e:
            elapsed_time = time() - start_time
            error_details = {
                'type': 'SMTP Recipients Refused',
                'message': 'Recipient email address was rejected',
                'details': str(e),
                'traceback': traceback.format_exc(),
                'suggestions': [
                    f'Check if {test_email} is a valid email address',
                    'Try with a different email address',
                ]
            }
            debug_log.append(f"[{elapsed_time:.2f}] ERROR: Recipients refused")
            messages.error(request, 'Recipient email rejected')

        except smtplib.SMTPException as e:
            elapsed_time = time() - start_time
            error_details = {
                'type': 'SMTP Exception',
                'message': 'General SMTP error occurred',
                'details': str(e),
                'traceback': traceback.format_exc(),
                'suggestions': [
                    'Check all SMTP settings in settings.py',
                    'Verify network connectivity to SMTP server',
                ]
            }
            debug_log.append(f"[{elapsed_time:.2f}] ERROR: SMTP exception")
            messages.error(request, f'SMTP error: {str(e)}')

        except (ConnectionError, OSError) as e:
            elapsed_time = time() - start_time
            error_details = {
                'type': 'Connection Error',
                'message': 'Failed to connect to SMTP server',
                'details': str(e),
                'traceback': traceback.format_exc(),
                'suggestions': [
                    'Check if Render can access smtp.sendgrid.net on port 587',
                    'Verify firewall/security group settings',
                    'Check if SMTP host and port are correct',
                ]
            }
            debug_log.append(f"[{elapsed_time:.2f}] ERROR: Connection error")
            messages.error(request, f'Connection error: {str(e)}')

        except Exception as e:
            elapsed_time = time() - start_time
            error_details = {
                'type': 'Unknown Error',
                'message': 'An unexpected error occurred',
                'details': str(e),
                'traceback': traceback.format_exc(),
                'suggestions': [
                    'Check the full traceback below for more details',
                    'Verify all email settings in settings.py',
                ]
            }
            debug_log.append(f"[{elapsed_time:.2f}] ERROR: {type(e).__name__}: {str(e)}")
            messages.error(request, f'Failed to send test email: {str(e)}')

    # Email configuration info
    email_config = {
        'backend': settings.EMAIL_BACKEND,
        'host': getattr(settings, 'EMAIL_HOST', 'Not set'),
        'port': getattr(settings, 'EMAIL_PORT', 'Not set'),
        'user': getattr(settings, 'EMAIL_HOST_USER', 'Not set'),
        'password_set': bool(getattr(settings, 'EMAIL_HOST_PASSWORD', None)),
        'password_length': len(getattr(settings, 'EMAIL_HOST_PASSWORD', '')) if getattr(settings, 'EMAIL_HOST_PASSWORD', None) else 0,
        'use_tls': getattr(settings, 'EMAIL_USE_TLS', 'Not set'),
        'use_ssl': getattr(settings, 'EMAIL_USE_SSL', 'Not set'),
        'timeout': getattr(settings, 'EMAIL_TIMEOUT', 'Not set'),
        'connection_timeout': getattr(settings, 'EMAIL_CONNECTION_TIMEOUT', 'Not set'),
        'from_email': settings.DEFAULT_FROM_EMAIL,
    }

    # Environment info
    env_info = {
        'environment': os.getenv('ENVIRONMENT', 'Not set'),
        'render': os.getenv('RENDER', 'Not set'),
        'debug': settings.DEBUG,
        'email_address_set': bool(os.getenv('EMAIL_ADDRESS')),
        'email_password_set': bool(os.getenv('EMAIL_HOST_PASSWORD')),
        'sendgrid_api_key_set': bool(os.getenv('SENDGRID_API_KEY')),
        'sendgrid_api_key_length': len(os.getenv('SENDGRID_API_KEY', '')),
        'sendgrid_api_key_starts_with': os.getenv('SENDGRID_API_KEY', '')[:3] if os.getenv('SENDGRID_API_KEY') else 'N/A',
        'postgres_locally': os.getenv('POSTGRES_LOCALLY', 'Not set'),
    }

    # All environment variables (for debugging)
    all_env_vars = {k: v for k, v in os.environ.items() if 'EMAIL' in k or 'ENVIRONMENT' in k or 'RENDER' in k or 'SENDGRID' in k}

    context = {
        'email_config': email_config,
        'env_info': env_info,
        'all_env_vars': all_env_vars,
        'debug_log': debug_log,
        'error_details': error_details,
    }

    return render(request, 'authentication/debug_email.html', context)

# -----------------------------
# Email verification resend - FIXED VERSION
# -----------------------------
def resend_verification(request):
    """Resend email verification with proper message handling"""
    
    if request.method == 'POST':
        # Get email from form or session
        email = request.POST.get('email') or request.session.get('unverified_email')
        
        if not email:
            messages.error(request, 'Please provide your email address.')
            return render(request, 'account/verification_sent.html')
        
        try:
            user = User.objects.get(email=email)
            
            # Get or create EmailAddress object
            email_address, created = EmailAddress.objects.get_or_create(
                user=user, 
                email=email,
                defaults={'primary': True, 'verified': False}
            )
            
            # Check if email is already verified
            if email_address.verified:
                messages.info(request, 'Your email is already verified! You can log in now.')
                request.session.pop('unverified_email', None)
                return redirect('account_login')
            
            # Create and send confirmation
            confirmation = EmailConfirmation.create(email_address)
            confirmation.send(request, signup=False)
            
            messages.success(request, f'New verification email sent to {email}! Please check your inbox and spam folder.')
            request.session['unverified_email'] = email
            
            # Render the same template instead of redirecting to preserve messages
            return render(request, 'account/verification_sent.html', {
                'email_sent': True,
                'resend_success': True
            })
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
        except Exception as e:
            messages.error(request, 'Error sending verification email. Please try again.')
            print(f"Resend verification error: {e}")
        
        # Render template with error messages
        return render(request, 'account/verification_sent.html')
    
    # GET request - show the resend form
    return render(request, 'account/verification_sent.html')

class CustomConfirmEmailView(ConfirmEmailView):
    def get(self, request, *args, **kwargs):
        """Handle GET confirmation and set session flag"""
        response = super().get(request, *args, **kwargs)
        
        if isinstance(response, HttpResponseRedirect):
            print("🎉 EMAIL CONFIRMED - Setting welcome flag in session!")
            
            # Set session flag instead of message
            request.session['show_welcome_popup'] = True
            request.session.save()
            print("📨 Welcome flag set in session!")
            
            # Replicate the redirect_to_dashboard logic
            try:
                profile, _ = UserProfile.objects.get_or_create(user=request.user)
                role = profile.role
                
                # Store profile info in session for session-based auth
                request.session['user_profile_id'] = profile.id
                request.session.save()
                
                print(f"🎯 Redirecting to dashboard with session flag set")
                return redirect('dashboard_signed_with_role')
                
            except Exception as e:
                print(f"❌ Error in direct dashboard redirect: {e}")
                return redirect('/')
        
        return response
    
@login_required
@require_POST
def clear_welcome_flag(request):
    profile = request.user.userprofile
    if not profile.has_seen_welcome:
        profile.has_seen_welcome = True
        profile.save()
    return JsonResponse({"status": "ok"})

# Add this view for the verification sent page
def verification_sent(request):
    """Show verification sent confirmation page"""
    return render(request, 'account/verification_sent.html')


@login_required
@require_POST
def update_profile_name(request):
    """Update user's first and last name via AJAX"""
    try:
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        # Update user fields
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.save()
        
        return JsonResponse({
            'success': True,
            'first_name': first_name,
            'last_name': last_name
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
        
@login_required
@require_POST
def update_avatar(request):
    try:
        if 'avatar' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No file provided'})
        
        avatar_file = request.FILES['avatar']
        print(f"Uploading file: {avatar_file.name}")
        
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        print(f"Profile created: {created}")
        
        profile.avatar = avatar_file
        profile.save()
        print(f"Avatar saved: {profile.avatar.url}")
        print(f"Avatar name: {profile.avatar.name}")
        print(f"Avatar path: {profile.avatar.path}")
        
        # Test if file exists
        import os
        if os.path.exists(profile.avatar.path):
            print(f"File exists at: {profile.avatar.path}")
        else:
            print(f"File NOT found at: {profile.avatar.path}")
        
        avatar_url = profile.avatar.url
        print(f"Returning avatar_url: {avatar_url}")
        
        return JsonResponse({
            'success': True,
            'avatar_url': avatar_url
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})
    
@login_required
@require_POST
def update_profile_email(request):
    """Update user's email address"""
    try:
        new_email = request.POST.get('email', '').strip()
        
        if not new_email:
            return JsonResponse({'success': False, 'error': 'Email is required'})
        
        # Check if email already exists
        if CustomUser.objects.filter(email=new_email).exclude(id=request.user.id).exists():
            return JsonResponse({'success': False, 'error': 'Email already in use'})
        
        request.user.email = new_email
        request.user.save()
        
        # You might want to mark email as unverified and send verification
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
def calculate_project_progress(project_id):
    tasks = ProjectTask.objects.filter(project_id=project_id)
    total_weight = sum(t.weight for t in tasks) or Decimal("1")
    progress = Decimal("0")

    for t in tasks:
        latest_update = t.updates.filter(status='A').order_by('-reviewed_at').first()
        if latest_update:
            progress += (t.weight / total_weight) * Decimal(latest_update.progress_percent)

    return round(progress, 2)


# --- Redirect logged-in user to their dashboard with token ---

@login_required
def redirect_to_dashboard(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    role = profile.role

    # Store profile info in session for session-based auth
    request.session['user_profile_id'] = profile.id
    request.session.save()

    # Redirect to session-based dashboard
    try:
        return redirect('dashboard_signed_with_role')
    except:
        return redirect('dashboard')


@login_required
@verified_email_required
def dashboard_signed_with_role(request, token=None, role=None):
    # Use session-based authentication
    verified_profile = get_user_profile(request)
    
    if not verified_profile:
        return redirect("unauthorized")

    user_role = verified_profile.role
    projects = ProjectProfile.objects.none()

    # --- Fetch projects by role ---
    if user_role == "PM":
        projects = ProjectProfile.objects.filter(project_manager=verified_profile)
    elif user_role == "VO":
        try:
            user_email = verified_profile.user.email
            if user_email:
                matching_clients = Client.objects.filter(email=user_email)
                if matching_clients.exists():
                    projects = ProjectProfile.objects.filter(client__in=matching_clients)
        except Client.DoesNotExist:
            pass
    else:
        projects = ProjectProfile.objects.all()

    # --- Optimize queries like API ---
    projects = (
        projects
        .prefetch_related(
            "tasks__assigned_to__user",
            "budgets__allocations",
            "tasks__scope",
        )
        .select_related()
    )

    projects_data = []
    all_tasks = []
    today = timezone.now().date()

    for project in projects:
        # --- Budget calculations ---
        planned_budget = project.budgets.aggregate(
            total=models.Sum("planned_amount")
        )["total"] or 0

        allocated_budget = FundAllocation.objects.filter(
            project_budget__project=project
        ).aggregate(total=models.Sum("amount"))["total"] or 0

        approved_budget = float(project.approved_budget or 0)
        estimated_cost = float(project.estimated_cost or 0)
        spent = float(getattr(project, "expense", 0) or 0)

        # --- Planned progress calculation ---
        planned_progress = 0
        if project.start_date and project.target_completion_date:
            total_days = (project.target_completion_date - project.start_date).days
            elapsed_days = (today - project.start_date).days
            if total_days > 0:
                planned_progress = (elapsed_days / total_days) * 100
            planned_progress = max(0, min(100, planned_progress))

        # --- Project data ---
        project_data = {
            "id": project.id,
            "project_id": project.project_id,
            "project_name": project.project_name,
            "name": project.project_name,
            "description": project.description or "",
            "status": project.status,
            "location": project.location or "",
            "gps_coordinates": project.gps_coordinates or "",
            "city_province": project.city_province or "",
            "project_type": project.project_type.name if project.project_type else "",
            "progress": float(getattr(project, "progress", 0) or 0),
            "planned_progress": round(planned_progress, 1),
            "actual_progress": float(getattr(project, "progress", 0) or 0),
            "estimated_cost": estimated_cost,
            "budget_total": {
                "estimated": estimated_cost,
                "approved": approved_budget,
                "planned": float(planned_budget),
                "allocated": float(allocated_budget),
                "spent": spent,
                "remaining": max(0, approved_budget - spent),
                "utilization_rate": round((spent / approved_budget * 100) if approved_budget > 0 else 0, 1),
            },
            "start_date": project.start_date.isoformat() if project.start_date else None,
            "target_completion_date": project.target_completion_date.isoformat() if project.target_completion_date else None,
            "end_date": project.target_completion_date.isoformat() if project.target_completion_date else None,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            "task_summary": {
                "total": 0,
                "completed": 0,
                "in_progress": 0,
                "pending": 0,
                "overdue": 0,
            },
            "tasks": [],
        }

        # --- Task data ---
        for task in project.tasks.all():
            is_overdue = (
                task.end_date and
                task.end_date < today and
                task.status not in ['CP', 'completed']
            )

            days_remaining = None
            if task.end_date:
                delta = task.end_date - today
                days_remaining = delta.days

            task_data = {
                "id": task.id,
                "title": task.task_name,
                "description": task.description or "",
                "start": task.start_date.isoformat() if task.start_date else None,
                "end": task.end_date.isoformat() if task.end_date else None,
                "progress": float(task.progress or 0),
                "status": task.status,
                "weight": float(getattr(task, "weight", 0) or 0),
                "manhours": int(getattr(task, "manhours", 0) or 0),
                "duration_days": int(getattr(task, "duration_days", 0) or 0),
                "is_overdue": is_overdue,
                "days_remaining": days_remaining,
                "assignee": None,
                "scope": None,
                "priority": getattr(task, "priority", "medium"),
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            }

            if task.assigned_to and getattr(task.assigned_to, "user", None):
                full_name = (
                    task.assigned_to.user.get_full_name()
                    or f"{task.assigned_to.user.first_name} {task.assigned_to.user.last_name}".strip()
                ) or task.assigned_to.user.username
                task_data["assignee"] = {
                    "id": task.assigned_to.id,
                    "name": full_name,
                    "email": task.assigned_to.user.email,
                    "role": getattr(task.assigned_to, "role", "Project Member"),
                }

            if hasattr(task, "scope") and task.scope:
                task_data["scope"] = {
                    "id": task.scope.id,
                    "name": task.scope.name,
                    "weight": float(task.scope.weight or 0),
                }

            project_data["task_summary"]["total"] += 1
            if task.status in ["CP", "completed"]:
                project_data["task_summary"]["completed"] += 1
            elif task.status in ["IP", "in_progress", "ongoing"]:
                project_data["task_summary"]["in_progress"] += 1
            elif task.status in ["PL", "planned", "pending"]:
                project_data["task_summary"]["pending"] += 1
            if is_overdue:
                project_data["task_summary"]["overdue"] += 1

            project_data["tasks"].append(task_data)
            all_tasks.append({**task_data, "project_id": project.id, "project_name": project.project_name})

        projects_data.append(project_data)

    # --- Status counts ---
    status_counts = {
        "planned": projects.filter(status="PL").count(),
        "ongoing": projects.filter(status="OG").count(),
        "completed": projects.filter(status="CP").count(),
        "cancelled": projects.filter(status="CN").count(),
    }

    # --- Total projects ---
    total_projects = sum(status_counts.values()) or 1  # avoid division by zero

    # --- Status percentages for progress rings ---
    status_percentages = {
    "planned": int(status_counts["planned"] / total_projects * 100),
    "ongoing": int(status_counts["ongoing"] / total_projects * 100),
    "completed": int(status_counts["completed"] / total_projects * 100),
    "cancelled": int(status_counts["cancelled"] / total_projects * 100),
}
    # --- Task status counts ---
    task_status_counts = {
        "total": len(all_tasks),
        "completed": len([t for t in all_tasks if t["status"] in ["CP", "completed"]]),
        "in_progress": len([t for t in all_tasks if t["status"] in ["IP", "in_progress", "ongoing"]]),
        "pending": len([t for t in all_tasks if t["status"] in ["PL", "planned", "pending"]]),
        "overdue": len([t for t in all_tasks if t["is_overdue"]]),
    }

    # --- Metrics ---
    total_projects = len(projects_data)
    avg_progress = (
        sum(p["actual_progress"] for p in projects_data) / total_projects
        if total_projects > 0 else 0
    )

    total_budget_planned = sum(p["budget_total"]["planned"] for p in projects_data)
    total_budget_spent = sum(p["budget_total"]["spent"] for p in projects_data)
    total_budget_approved = sum(p["budget_total"]["approved"] for p in projects_data)

    task_completion_rate = (
        (task_status_counts["completed"] / task_status_counts["total"] * 100)
        if task_status_counts["total"] > 0 else 0
    )

    metrics = {
        "total_projects": total_projects,
        "avg_progress": round(avg_progress, 1),
        "total_budget_planned": total_budget_planned,
        "total_budget_approved": total_budget_approved,
        "total_budget_spent": total_budget_spent,
        "total_budget_remaining": max(0, total_budget_approved - total_budget_spent),
        "budget_utilization": round(
            (total_budget_spent / total_budget_approved * 100)
            if total_budget_approved > 0 else 0,
            1,
        ),
        "task_completion_rate": round(task_completion_rate, 1),
        "overdue_tasks": task_status_counts["overdue"],
    }

    projects_json = json.dumps(projects_data, cls=DjangoJSONEncoder)

    # If token was None, get it from session for context
    if token is None:
        token = request.session.get('dashboard_token')

    context = {
        "profile": verified_profile,
        "projects": projects_data,
        "projects_json": projects_json,
        "status_counts": status_counts,
        "status_percentages": status_percentages,
        "task_status_counts": task_status_counts,
        "metrics": metrics,
        "recent_tasks": sorted(
            all_tasks,
            key=lambda x: x["updated_at"] or x["created_at"] or "",
            reverse=True
        )[:10],
        "last_updated": timezone.now().isoformat(),
        "token": token,
        "role": verified_profile.role,
    }

    return render(request, "dashboard.html", context)



class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'account/password_change.html'
    form_class = StyledPasswordChangeForm
    success_url = reverse_lazy('account_change_password')

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, form.user)
        messages.success(self.request, "Your password has been changed successfully!")
        return super().form_valid(form)

@login_required
@verified_email_required
def profile(request):
    return render(request, 'account/profile.html')

@login_required
def email_verification_required(request):
    if request.user.emailaddress_set.filter(verified=True).exists():
        return redirect('profile')
    return render(request, 'account/verified_email_required.html')

def unauthorized(request):
    return render(request, 'account/unauthorized.html', status=403)
@login_required
@verified_email_required
def user_settings(request):
    return render(request, 'account/settings.html', status=403)

def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


@login_required
@role_required('EG', 'OM')
def manage_user_profiles(request, token=None):
    # For session-based access (token=None), use the user's profile directly
    # since @role_required already verified the user has the right role
    if token is None:
        try:
            verified_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            messages.error(request, "User profile not found. Please contact support.")
            return redirect("unauthorized")
    else:
        # For session-based access, get user profile
        verified_profile = get_user_profile(request)
        if not verified_profile:
            return redirect("unauthorized")
    
    if verified_profile.role == "EG":
        available_role_choices = UserProfile.ROLE_CHOICES
    else:
        available_role_choices = [
            (code, label) for code, label in UserProfile.ROLE_CHOICES 
            if code != "EG"
        ]

    # Get filter and pagination parameters
    search_query = request.GET.get("q", "")
    role_filter = request.GET.get("role", "")
    archived_filter = request.GET.get("archived", "0")  # "0", "1", or "all"
    per_page = int(request.GET.get("per_page", 25))
    page_number = request.GET.get("page", 1)
    
    # Validate per_page
    if per_page not in [10, 25, 50, 100]:
        per_page = 25

    # For backward compatibility
    show_archived = archived_filter == "1"

    profiles = UserProfile.objects.select_related('user').exclude(id=verified_profile.id)

    # Apply search filter
    if search_query:
        profiles = profiles.filter(
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )

    if role_filter:
        profiles = profiles.filter(role=role_filter)

    # Enhanced archived filter logic
    if archived_filter == "1":  # Show only archived
        profiles = profiles.filter(is_archived=True)
    elif archived_filter == "all":  # Show both archived and active
        pass  # No filter needed
    else:  # Default: show only active (archived_filter == "0")
        profiles = profiles.filter(is_archived=False)

    # Order by updated_at (most recent first) for better UX
    profiles = profiles.order_by('-updated_at', '-id')

    # Get total count before pagination
    total_users = profiles.count()

    # Handle inline updates
    if request.method == "POST":
        profile_id = request.POST.get("profile_id")
        profile = get_object_or_404(UserProfile, id=profile_id)

        if profile.is_archived:
            messages.warning(request, f"Cannot update archived user {profile.user.email}.")
        else:
            # Update role if sent
            role = request.POST.get("role")
            if role and role != profile.role:
                old_role = profile.get_role_display()
                profile.role = role
                # Update the updated_at timestamp
                profile.updated_at = timezone.now()
                messages.success(request, f"{profile.user.email}'s role updated from {old_role} to {profile.get_role_display()}.")

            # Update first and last name if sent
            first_name = request.POST.get("first_name")
            last_name = request.POST.get("last_name")
            
            if first_name is not None or last_name is not None:
                old_name = f"{profile.user.first_name} {profile.user.last_name}".strip()
                
                if first_name is not None:
                    profile.user.first_name = first_name.strip()
                if last_name is not None:
                    profile.user.last_name = last_name.strip()
                
                new_name = f"{profile.user.first_name} {profile.user.last_name}".strip()
                
                profile.user.save()
                # Update the updated_at timestamp
                profile.updated_at = timezone.now()
                
                if old_name != new_name:
                    if new_name:
                        messages.success(request, f"Name updated to '{new_name}' for {profile.user.email}.")
                    else:
                        messages.success(request, f"Name cleared for {profile.user.email}.")
                else:
                    messages.info(request, f"No changes made to {profile.user.email}'s name.")

            profile.save()

        # Redirect to prevent form resubmission but preserve current page and filters
        redirect_params = []
        if search_query:
            redirect_params.append(f"q={search_query}")
        if role_filter:
            redirect_params.append(f"role={role_filter}")
        if archived_filter != "0":
            redirect_params.append(f"archived={archived_filter}")
        if per_page != 25:
            redirect_params.append(f"per_page={per_page}")
        if page_number != "1":
            redirect_params.append(f"page={page_number}")
        
        redirect_url = request.path
        if redirect_params:
            redirect_url += "?" + "&".join(redirect_params)
        
        return redirect(redirect_url)

    # Pagination
    paginator = Paginator(profiles, per_page)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Get analytics data for dashboard
    analytics = get_user_analytics(verified_profile)

    context = {
        "profiles": page_obj,
        'ROLE_CHOICES': available_role_choices,
        "search_query": search_query,
        "role_filter": role_filter,
        "token": token,
        "show_archived": show_archived,  # For backward compatibility
        "archived_filter": archived_filter,  # New enhanced filter
        "per_page": per_page,
        "total_users": total_users,
        "analytics": analytics,
    }

    return render(request, "users/manage_user_profiles.html", context)


def get_user_analytics(verified_profile):
    """
    Get analytics data for the user management dashboard using your exact model fields
    """
    now = timezone.now()
    last_30_days = now - timedelta(days=30)
    last_7_days = now - timedelta(days=7)
    
    # Base queryset excluding the current user and superusers
    base_queryset = UserProfile.objects.exclude(
        Q(id=verified_profile.id) | Q(user__is_superuser=True)
    )
    
    analytics = {
        'total_users': base_queryset.count(),
        'active_users': base_queryset.filter(is_archived=False).count(),
        'archived_users': base_queryset.filter(is_archived=True).count(),
        # Use user__date_joined instead of created_at
        'new_users_30_days': base_queryset.filter(
            user__date_joined__gte=last_30_days
        ).count(),
        'recently_updated': base_queryset.filter(
            updated_at__gte=last_30_days
        ).count(),
    }
    
    return analytics

    
@login_required
@role_required("EG", "OM")
def add_user(request, token=None):
    # For session-based access (token=None), use the user's profile directly
    # since @role_required already verified the user has the right role
    if token is None:
        try:
            verified_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            messages.error(request, "User profile not found. Please contact support.")
            return redirect("unauthorized")
    else:
        # For session-based access, get user profile
        verified_profile = get_user_profile(request)
        if not verified_profile:
            return redirect("unauthorized")
   
    if not request.user.is_superuser and verified_profile.role not in ["OM", "EG" ]:
        print("Unauthorized: Not superuser or EG")
        messages.error(request, "Access denied. You are not authorized to add users.")
        return redirect("unauthorized")
    
    if verified_profile.role == "EG":
        available_role_choices = UserProfile.ROLE_CHOICES
    else:
        available_role_choices = [
            (code, label) for code, label in UserProfile.ROLE_CHOICES 
            if code != "EG"
        ]
    
    if request.method == "POST":
        print("POST data:", request.POST)

        email = request.POST.get("email")
        password = request.POST.get("password")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        role = request.POST.get("role")

        print("Collected fields:", email, first_name, last_name, role)

        if not email or not password or not first_name or not last_name:
            print("Error: Missing required fields")
            messages.error(request, "Email, password, first name, and last name are required.")
        elif CustomUser.objects.filter(email=email).exists():
            print("Error: Email already exists ->", email)
            messages.error(request, "Email already exists.")
        else:
            print("Creating user...")
            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            print("User created:", user)

            # Ensure UserProfile is created or updated
            if role:
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.role = role
                profile.save()
                print("Profile saved with role:", role, "| Created new?", created)

            messages.success(request, f"User '{first_name} {last_name}' with email '{email}' created successfully.")
            print("Success: User created and profile updated.")
            # Do NOT consume messages here!
            return redirect("manage_user_profiles", token=token)

    
    print("Rendering add_user.html")
    return render(request, "users/add_user.html", {
        "token": token,
        'ROLE_CHOICES': available_role_choices,
    })

@login_required
@role_required("EG", "OM")
def edit_user(request, token=None, user_id=None):
    # For session-based access (token=None), use the user's profile directly
    if token is None:
        try:
            verified_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            messages.error(request, "User profile not found. Please contact support.")
            return redirect("unauthorized")
    else:
        # For session-based access, get user profile
        verified_profile = get_user_profile(request)
        if not verified_profile:
            return redirect("unauthorized")
    
    # Check role permissions
    if not request.user.is_superuser and verified_profile.role not in ["OM", "EG"]:
        messages.error(request, "Access denied. You are not authorized to edit users.")
        return redirect("unauthorized")

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        user.email = request.POST.get("email")
        new_password = request.POST.get("password")
        if new_password:
            user.set_password(new_password)

        user.save()

        messages.success(request, f"User '{user.email}' updated successfully.")
        return redirect("manage_user_profiles", token=token)

    return render(request, "users/edit_user.html", {
        "user_obj": user,
        "token": token,
    })

@login_required
@role_required('EG', 'OM')
def archive_user(request, token=None, user_id=None):
    # For session-based access (token=None), use the user's profile directly
    if token is None:
        try:
            verified_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            messages.error(request, "User profile not found. Please contact support.")
            return redirect("unauthorized")
    else:
        # For session-based access, get user profile
        verified_profile = get_user_profile(request)
        if not verified_profile:
            return redirect("unauthorized")
    
    # Check role permissions (only EG can archive users)
    if not request.user.is_superuser and verified_profile.role != "EG":
        messages.error(request, "Access denied. Only Engineering Group can archive users.")
        return redirect("unauthorized")

    profile = get_object_or_404(UserProfile, user_id=user_id)

    if request.method == "POST":
        profile.is_archived = True
        profile.save()
        messages.info(request, f"User '{profile.user.email}' has been archived (View Only).")
        return redirect("manage_user_profiles", token=token)

    return render(request, "users/archive_user.html", {
        "profile": profile,
        "token": token,
    })

@login_required
@role_required('EG', 'OM')
def unarchive_user(request, token=None, user_id=None):
    # For session-based access (token=None), use the user's profile directly
    if token is None:
        try:
            verified_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            messages.error(request, "User profile not found. Please contact support.")
            return redirect("unauthorized")
    else:
        # For session-based access, get user profile
        verified_profile = get_user_profile(request)
        if not verified_profile:
            return redirect("unauthorized")
    
    # Check role permissions (only EG can unarchive users)
    if not request.user.is_superuser and verified_profile.role != "EG":
        messages.error(request, "Access denied. Only Engineering Group can unarchive users.")
        return redirect("unauthorized")

    profile = get_object_or_404(UserProfile, user_id=user_id)
    profile.is_archived = False
    profile.save()

    messages.success(request, f"User '{profile.user.username}' has been unarchived.")
    return redirect("manage_user_profiles", token=token)

@login_required
@superuser_required
def search_users(request):
    q = request.GET.get('q', '').strip()
    role = request.GET.get('role', '')
    
    users = UserProfile.objects.select_related('user')
    
    if q:
        users = users.filter(
            Q(user__username__icontains=q) |
            Q(full_name__icontains=q) |
            Q(user__email__icontains=q)
        )
    if role:
        users = users.filter(role=role)

    users = users[:20]  # limit for performance

    results = []
    for u in users:
        if not u.user:  # skip broken profiles
            continue
        results.append({
            'id': u.id,
            'username': u.user.username,
            'full_name': u.full_name or '',
            'email': u.user.email or '',
            'role': u.role or '',
        })

    return JsonResponse(results, safe=False)

@login_required
@require_http_methods(["GET"])
def dashboard_api(request):
    """
    API endpoint for dashboard real-time updates.
    Returns project data and status counts in JSON format with enhanced task tracking.
    """
    token = request.GET.get("token")
    role = request.GET.get("role")

    # Use session-based authentication
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return JsonResponse({"success": False, "error": "User not authenticated"}, status=403)

    # --- Filter projects by role ---
    projects = ProjectProfile.objects.none()
    user_role = verified_profile.role

    if user_role == "PM":
        projects = ProjectProfile.objects.filter(project_manager=verified_profile)
    elif user_role == "VO":
        try:
            user_email = verified_profile.user.email
            if user_email:
                matching_clients = Client.objects.filter(email=user_email)
                if matching_clients.exists():
                    projects = ProjectProfile.objects.filter(client__in=matching_clients)
        except Client.DoesNotExist:
            pass
    else:
        # Admin / EG / etc.
        projects = ProjectProfile.objects.all()

    # --- Optimize queries ---
    projects = (
        projects.prefetch_related(
            "tasks__assigned_to__user",
            "budgets__allocations",
            "tasks__scope",
        )
        .select_related()
    )

    projects_data = []
    all_tasks = []
    today = timezone.now().date()

    for project in projects:
        # ---- Budget calculations ----
        planned_budget = project.budgets.aggregate(
            total=models.Sum("planned_amount")
        )["total"] or 0

        allocated_budget = FundAllocation.objects.filter(
            project_budget__project=project
        ).aggregate(total=models.Sum("amount"))["total"] or 0

        approved_budget = float(project.approved_budget or 0)
        estimated_cost = float(project.estimated_cost or 0)
        spent = float(getattr(project, "expense", 0) or 0)

        # --- Planned progress calculation ---
        planned_progress = 0
        if project.start_date and project.target_completion_date:
            total_days = (project.target_completion_date - project.start_date).days
            elapsed_days = (today - project.start_date).days
            if total_days > 0:
                planned_progress = (elapsed_days / total_days) * 100
        planned_progress = max(0, min(100, planned_progress))

        # ---- Project data ----
        project_data = {
            "id": project.id,
            "project_id": project.project_id,
            "project_name": project.project_name,
            "name": project.project_name,
            "description": project.description or "",
            "status": project.status,
            "location": project.location or "",
            "gps_coordinates": project.gps_coordinates or "",
            "city_province": project.city_province or "",
            "project_type": project.project_type.name if project.project_type else "",
            "progress": float(getattr(project, "progress", 0) or 0),
            "planned_progress": round(planned_progress, 1),
            "actual_progress": float(getattr(project, "progress", 0) or 0),
            "estimated_cost": estimated_cost,
            "budget_total": {
                "estimated": estimated_cost,
                "approved": approved_budget,
                "planned": float(planned_budget),
                "allocated": float(allocated_budget),
                "spent": spent,
                "remaining": max(0, approved_budget - spent),
                "utilization_rate": round(
                    (spent / approved_budget * 100) if approved_budget > 0 else 0, 1
                ),
            },
            "start_date": project.start_date.isoformat() if project.start_date else None,
            "target_completion_date": project.target_completion_date.isoformat() if project.target_completion_date else None,
            "end_date": project.target_completion_date.isoformat() if project.target_completion_date else None,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            "task_summary": {
                "total": 0,
                "completed": 0,
                "in_progress": 0,
                "pending": 0,
                "overdue": 0,
            },
            "tasks": [],
        }

        # ---- Task data ----
        project_tasks = project.tasks.all()
        for task in project_tasks:
            is_overdue = (
                task.end_date
                and task.end_date < timezone.now().date()
                and task.status not in ["CP", "completed"]
            )

            days_remaining = None
            if task.end_date:
                delta = task.end_date - timezone.now().date()
                days_remaining = delta.days

            task_data = {
                "id": task.id,
                "title": task.task_name,
                "description": task.description or "",
                "start": task.start_date.isoformat() if task.start_date else None,
                "end": task.end_date.isoformat() if task.end_date else None,
                "progress": float(task.progress or 0),
                "status": task.status,
                "weight": float(getattr(task, "weight", 0) or 0),
                "manhours": int(getattr(task, "manhours", 0) or 0),
                "duration_days": int(getattr(task, "duration_days", 0) or 0),
                "is_overdue": is_overdue,
                "days_remaining": days_remaining,
                "assignee": None,
                "scope": None,
                "priority": getattr(task, "priority", "medium"),
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            }

            if task.assigned_to and getattr(task.assigned_to, "user", None):
                full_name = (
                    task.assigned_to.user.get_full_name()
                    or f"{task.assigned_to.user.first_name} {task.assigned_to.user.last_name}".strip()
                ) or task.assigned_to.user.username
                task_data["assignee"] = {
                    "id": task.assigned_to.id,
                    "name": full_name,
                    "email": task.assigned_to.user.email,
                    "role": getattr(task.assigned_to, "role", "Project Member"),
                }

            if hasattr(task, "scope") and task.scope:
                task_data["scope"] = {
                    "id": task.scope.id,
                    "name": task.scope.name,
                    "weight": float(task.scope.weight or 0),
                }

            project_data["task_summary"]["total"] += 1
            if task.status in ["CP", "completed"]:
                project_data["task_summary"]["completed"] += 1
            elif task.status in ["IP", "in_progress", "ongoing"]:
                project_data["task_summary"]["in_progress"] += 1
            elif task.status in ["PL", "planned", "pending"]:
                project_data["task_summary"]["pending"] += 1
            if is_overdue:
                project_data["task_summary"]["overdue"] += 1

            project_data["tasks"].append(task_data)
            all_tasks.append({**task_data, "project_id": project.id, "project_name": project.project_name})

        projects_data.append(project_data)

    # ---- Status + task counts ----
    status_counts = {
        "planned": projects.filter(status="PL").count(),
        "ongoing": projects.filter(status="OG").count(),
        "completed": projects.filter(status="CP").count(),
        "cancelled": projects.filter(status="CN").count(),
    }

    # Calculate status percentages (matching dashboard view)
    total_projects = len(projects_data)
    status_percentages = {}
    if total_projects > 0:
        for status, count in status_counts.items():
            status_percentages[status] = round((count / total_projects) * 100, 1)
    else:
        status_percentages = {"planned": 0, "ongoing": 0, "completed": 0, "cancelled": 0}

    task_status_counts = {
        "total": len(all_tasks),
        "completed": len([t for t in all_tasks if t["status"] in ["CP", "completed"]]),
        "in_progress": len([t for t in all_tasks if t["status"] in ["IP", "in_progress", "ongoing"]]),
        "pending": len([t for t in all_tasks if t["status"] in ["PL", "planned", "pending"]]),
        "overdue": len([t for t in all_tasks if t["is_overdue"]]),
    }

    total_projects = len(projects_data)
    avg_progress = (
        sum(p["actual_progress"] for p in projects_data) / total_projects if total_projects > 0 else 0
    )
    total_budget_planned = sum(p["budget_total"]["planned"] for p in projects_data)
    total_budget_spent = sum(p["budget_total"]["spent"] for p in projects_data)
    total_budget_approved = sum(p["budget_total"]["approved"] for p in projects_data)

    task_completion_rate = (
        (task_status_counts["completed"] / task_status_counts["total"] * 100)
        if task_status_counts["total"] > 0 else 0
    )

    response_data = {
        "success": True,
        "projects": projects_data,
        "status_counts": status_counts,
        "status_percentages": status_percentages,
        "task_status_counts": task_status_counts,
        "metrics": {
            "total_projects": total_projects,
            "avg_progress": round(avg_progress, 1),
            "total_budget_planned": total_budget_planned,
            "total_budget_approved": total_budget_approved,
            "total_budget_spent": total_budget_spent,
            "total_budget_remaining": max(0, total_budget_approved - total_budget_spent),
            "budget_utilization": round(
                (total_budget_spent / total_budget_approved * 100) if total_budget_approved > 0 else 0, 1
            ),
            "task_completion_rate": round(task_completion_rate, 1),
            "overdue_tasks": task_status_counts["overdue"],
        },
        "recent_tasks": sorted(
            all_tasks, key=lambda x: x["updated_at"] or x["created_at"] or "", reverse=True
        )[:10],
        "last_updated": timezone.now().isoformat(),
        "timestamp": timezone.now().timestamp(),
    }

    return JsonResponse(response_data)

@require_POST
def clear_toast_session(request):
    """Clear the toast session data after displaying it - Centralized for all apps"""
    if 'show_toast' in request.session:
        del request.session['show_toast']
        request.session.save()
    return JsonResponse({'success': True})