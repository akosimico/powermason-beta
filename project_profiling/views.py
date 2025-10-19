from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.signing import BadSignature, SignatureExpired
# Removed token imports as they are no longer needed
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from datetime import timedelta
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from decimal import Decimal, InvalidOperation
from django.db import models
from django.db.models import Sum, Max
from datetime import date, datetime
from django.urls import reverse
from django.utils.timezone import localtime
import json
from django.conf import settings
from django.core.files import File
import os
import random
import requests
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST
from notifications.utils import send_notification
from notifications.models import Notification, NotificationStatus
from authentication.models import UserProfile
from authentication.utils.tokens import get_user_profile, verify_user_profile
from authentication.utils.toast_helpers import set_toast_message, set_toast_from_messages
from django.forms.models import model_to_dict
from authentication.utils.decorators import verified_email_required, role_required
from .forms import ProjectProfileForm, ProjectBudgetForm
from django.urls import resolve
from .models import ProjectProfile, ProjectFile, ProjectBudget, FundAllocation, ProjectStaging, ProjectType, ProjectScope, Expense, ProjectDocument
from manage_client.models import Client
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from powermason_capstone.utils.calculate_progress import calculate_progress

# Import cost tracking views
from .cost_tracking_views import (
    subcontractor_list, api_subcontractor_list, api_subcontractor_detail,
    api_subcontractor_payments, api_create_payment,
    mobilization_costs, api_mobilization_costs_list,
    api_create_mobilization_cost, api_mobilization_cost_detail
)
# ----------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------
def get_next_project_id(project_type):
    """Generate the next project ID for the given project type."""
    last_project = ProjectProfile.objects.filter(project_source=project_type).aggregate(Max("project_id"))
    last_id = last_project["project_id__max"]
    if last_id:
        try:
            prefix = project_type
            number = int(str(last_id).replace(f"{prefix}-", ""))
            return f"{prefix}-{number+1:03d}"
        except Exception:
            return f"{project_type}-001"
    else:
        return f"{project_type}-001"

def get_project_form_class(project_type):
    """Get the appropriate form class based on project type."""
    return ProjectProfileForm

# Source labels mapping
SOURCE_LABELS = {
    'DC': 'Direct Client',
    'GC': 'General Contractor',
}

# ----------------------------------------
# FUNCTION
# ----------------------------------------
@login_required
@verified_email_required
@role_required('OM', 'EG')
def search_project_managers(request):
    query = request.GET.get('q', '')
    project_managers = UserProfile.objects.filter(role='PM').select_related("user")

    if query:
        # Filter by actual database fields only
        project_managers = project_managers.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query)
        )

    data = []
    for u in project_managers:
        # Construct full_name from the related User model
        full_name = f"{u.user.first_name} {u.user.last_name}".strip()
        # If that results in empty string, use username as fallback
        if not full_name:
            full_name = u.user.username
            
        data.append({
            "id": u.id,
            "full_name": full_name,
            "email": u.user.email,
            "avatar": str(u.avatar) if u.avatar else None,  # Add avatar field
        })
    
    return JsonResponse(data, safe=False)


# ----------------------------------------
# PROJECTS LISTS / CREATE / EDIT / DELETE
# ----------------------------------------

@login_required
def project_list_default(request):
    
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    # Redirect to session-based project list
    return redirect('project_list')

@login_required
@verified_email_required
@role_required('PM', 'OM', 'EG', 'VO')
def project_list_signed_with_role(request):
    # Get user profile from session
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    # Handle file upload
    if request.method == "POST" and "project_id" in request.POST:
        project_id = request.POST.get("project_id")
        project = get_object_or_404(ProjectProfile, id=project_id)

        if role == "PM" and project.project_manager != verified_profile:
            return HttpResponse("Unauthorized upload")
        if role == "OM" and not (project.created_by == verified_profile or project.assigned_to == verified_profile):
            return HttpResponse("Unauthorized upload")

        files = request.FILES.getlist("file")
        for f in files:
            ProjectFile.objects.create(project=project, file=f)

        return redirect("project_list")

    # Fetch projects (exclude archived ones)
    if verified_profile.role in ['EG', 'OM']:
        projects = ProjectProfile.objects.filter(archived=False)

    elif verified_profile.role == 'PM':
        projects = ProjectProfile.objects.filter(
        project_manager=verified_profile,
        archived=False
    )

    elif verified_profile.role == 'VO':
    # Match client by email
        client_email = verified_profile.user.email
        try:
            client = Client.objects.get(email__iexact=client_email)
            projects = ProjectProfile.objects.filter(
            client=client,
            archived=False
            )
        except Client.DoesNotExist:
        # No client matching this email
            projects = ProjectProfile.objects.none()

    context = {
        'user_uuid': verified_profile.user.id,
        'role': verified_profile.role,
        'projects': projects,
    }
    return render(request, 'project_profiling/project_list.html', context)

@login_required
@verified_email_required
@role_required('OM', 'EG')
def project_costing_dashboard(request):
    # Get user profile from session
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    projects = ProjectProfile.objects.all()

    projects_with_totals = []
    grand_total_planned = 0
    grand_total_allocated = 0

    for project in projects:
        # Sum of planned amounts
        total_planned = project.budgets.aggregate(total=Sum('planned_amount'))['total'] or 0

        # Sum of all allocations across categories
        total_allocated = sum(
            budget.allocations.filter(is_deleted=False).aggregate(total=Sum('amount'))['total'] or 0
            for budget in project.budgets.all()
        )

        # Sum of all actual spending (from Expense model)
        total_spent = project.expenses.aggregate(total=Sum('amount'))['total'] or 0

        # Calculate utilization percentage
        utilization = (total_spent / total_allocated * 100) if total_allocated > 0 else 0

        projects_with_totals.append({
            "project": project,
            "total_planned": total_planned,
            "total_allocated": total_allocated,
            "total_spent": total_spent,
            "remaining": total_allocated - total_spent,
            "utilization": utilization,
        })

        grand_total_planned += total_planned
        grand_total_allocated += total_allocated

    context = {
        "projects_with_totals": projects_with_totals,
        "grand_total_budget": grand_total_planned,
        "grand_total_allocated": grand_total_allocated,
        "role": verified_profile.role,
    }
    return render(request, "project_profiling/project_costing_dashboard.html", context)


def general_projects_list(request):
    # Get user profile from session
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    # Use profile role
    role = verified_profile.role

    # Toggle: show archived or active projects
    show_archived = request.GET.get('archived') == '1'
    projects = ProjectProfile.objects.filter(
        archived=show_archived,
        project_source="GC"
    )
    
    # Get pending projects for General Contractor
    pending_projects = ProjectStaging.objects.filter(
        status="PL", 
        is_draft=False,
        project_data__project_source="GC"
    ).order_by('-submitted_at')
    
    # Calculate total approved budget
    total_budget = projects.aggregate(
        total=models.Sum('approved_budget')
    )['total'] or 0
    
    return render(request, "project_profiling/general_project_list.html", {
        "projects": projects,
        "pending_projects": pending_projects,
        "url_name": resolve(request.path_info).url_name,  
        "project_type": "GC",
        "show_archived": show_archived,
        "total_budget": total_budget
    })
    
@role_required('OM', 'EG')
def project_unarchive_signed_with_role(request, project_type, pk):
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    # --- Fetch project ---
    if request.user.is_superuser or verified_profile.role in ['EG', 'OM']:
        # Superusers, Engineers, and Operations Managers can unarchive any project
        project = get_object_or_404(ProjectProfile, pk=pk)
    else:  # PM (Project Manager) can only unarchive their own projects
        project = get_object_or_404(
            ProjectProfile.objects.filter(
                Q(created_by=verified_profile) |
                Q(project_manager=verified_profile),
                pk=pk
            )
        )

    # --- Handle unarchive action ---
    if request.method == 'POST':
        project.archived = False
        project.save()
        messages.success(request, f"Project '{project.project_name}' has been unarchived.")

        if project.project_source == "GC":
            return redirect("project_list_general_contractor")
        else:
            return redirect("project_list_direct_client")

    return render(request, 'project_profiling/project_confirm_unarchive.html', {
        'project': project,
        'project_type': project_type,
    })

    
def archived_projects_list(request, project_type):
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    projects = ProjectProfile.objects.filter(archived=True, project_source=project_type)
    
    return render(request, "project_profiling/general_project_list.html", {
        "projects": projects,
        "project_type": project_type,
        
    })

def direct_projects_list(request):
    # Get user profile from session
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    # Use profile role
    role = verified_profile.role

    # Toggle: show archived or active projects
    show_archived = request.GET.get('archived') == '1'
    projects = ProjectProfile.objects.filter(
        archived=show_archived,
        project_source="DC"
    )
    
    # Get pending projects for Direct Client
    pending_projects = ProjectStaging.objects.filter(
        status="PL", 
        is_draft=False,
        project_data__project_source="DC"
    ).order_by('-submitted_at')
    
    # Calculate total approved budget
    total_budget = projects.aggregate(
        total=models.Sum('approved_budget')
    )['total'] or 0
    
    return render(request, "project_profiling/direct_project_list.html", {
        "projects": projects,
        "pending_projects": pending_projects,
        "url_name": resolve(request.path_info).url_name,  
        "project_type": "DC",
        "show_archived": show_archived,
        "total_budget": total_budget
    })

def update_project_status(request, project_id):
    if request.method == "POST":
        # Get user profile from session
        verified_profile = get_user_profile(request)
        if isinstance(verified_profile, HttpResponseRedirect):
            return verified_profile
        if verified_profile is None or getattr(verified_profile, 'role', None) is None:
            return redirect('unauthorized')  # safe fallback

        # Fetch the project
        project = get_object_or_404(ProjectProfile, id=project_id)

        # Update status if valid
        new_status = request.POST.get("status")
        if new_status in dict(ProjectProfile.STATUS_CHOICES):
            project.status = new_status
            project.save()
            messages.success(request, f"Status updated to {project.get_status_display()}.")
        else:
            messages.error(request, "Invalid status selected.")

    # Redirect back to the referring page
    return redirect(request.META.get('HTTP_REFERER', 'project_list'))


@login_required
@verified_email_required
def project_view(request, project_source, pk):
    # Verify the user
    verified_profile = get_user_profile(request)
    
    if not verified_profile:
        return redirect("unauthorized")

    if verified_profile is None:
        return redirect('unauthorized') 

    user_role = getattr(verified_profile, 'role', None)
    if user_role is None:
        return redirect('unauthorized')  

    # Use user_role instead of role
    if user_role == "PM":
        project = get_object_or_404(ProjectProfile, pk=pk, project_manager=verified_profile)
    else:
        project = get_object_or_404(ProjectProfile, pk=pk)

    project.timeline_progress = calculate_progress(project.start_date, project.target_completion_date)
    request.session['project_return_url'] = request.get_full_path()
    request.session['task_list_return_url'] = request.get_full_path()
    
    return render(request, 'project_profiling/project_view.html', {
        'project': project,
        'role': user_role,  # always valid
        'project_source': project_source,
        'current_project_id': pk,
    })


@login_required
@verified_email_required
def draft_projects_list(request):
    """Display list of draft projects that user can continue editing."""
    user_profile = get_object_or_404(UserProfile, user=request.user)

    # Get draft projects for this user
    draft_projects = ProjectStaging.objects.filter(
        created_by=user_profile,
        is_draft=True,
        submitted_for_approval=False
    ).order_by('-submitted_at')

    return render(request, "project_profiling/draft_projects_list.html", {
        "projects": draft_projects,
        "role": user_profile.role,
    })

@login_required
@verified_email_required
def edit_draft_project(request, draft_id):
    """Edit a draft project using the existing project_edit.html template."""
    user_profile = get_object_or_404(UserProfile, user=request.user)

    # Get the draft project
    draft_project = get_object_or_404(ProjectStaging,
                                     id=draft_id,
                                     created_by=user_profile,
                                     is_draft=True)

    # Get client information
    client_id = draft_project.project_data.get("client_id") or draft_project.project_data.get("client")
    client = None
    if client_id:
        try:
            from manage_client.models import Client
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            pass

    if not client:
        messages.error(request, "Client information is missing for this draft.")
        return redirect('draft_projects_list')

    # Create form instance with draft data
    form_data = draft_project.project_data.copy()

    # Convert any stored IDs back to objects for the form
    if form_data.get('project_manager_id'):
        form_data['project_manager'] = form_data.pop('project_manager_id')
    if form_data.get('client_id'):
        form_data['client'] = form_data.pop('client_id')

    if request.method == "POST":
        form = ProjectProfileForm(request.POST, request.FILES, pre_selected_client_id=client.id)

        # Check if this is a draft save or final submission
        is_draft_save = request.POST.get('save_as_draft') == 'true'

        if is_draft_save:
            # Save as draft - less strict validation
            for field in form.fields.values():
                field.required = False

        if form.is_valid() or is_draft_save:
            # Prepare cleaned data
            cleaned_data = {}
            for k, v in request.POST.items():
                if k not in ['csrfmiddlewaretoken', 'save_as_draft']:
                    cleaned_data[k] = v

            # Handle file uploads
            for k, v in request.FILES.items():
                if hasattr(v, "read") and hasattr(v, "name"):
                    file_path = default_storage.save(f"{k}/{v.name}", v)
                    cleaned_data[k] = file_path

            if is_draft_save:
                # Update the existing draft
                draft_project.project_data = {
                    **cleaned_data,
                    'project_id': draft_project.project_data.get('project_id'),
                    'client_id': client.id,
                }
                draft_project.submitted_at = timezone.now()
                draft_project.save()

                messages.success(request, "Draft updated successfully!")
                return redirect('draft_projects_list')
            else:
                # Final submission - convert draft to pending project
                draft_project.is_draft = False
                draft_project.submitted_for_approval = True
                draft_project.project_data = {
                    **{k: serialize_field(v) for k, v in form.cleaned_data.items()},
                    'project_manager_id': form.cleaned_data.get('project_manager').id if form.cleaned_data.get('project_manager') else None,
                    'client_id': client.id,
                    'project_id': draft_project.project_data.get('project_id'),
                }
                draft_project.submitted_at = timezone.now()
                draft_project.save()

                messages.success(request, f"Project '{form.cleaned_data.get('project_name', 'Unnamed')}' submitted for approval!")
                return redirect('pending_projects_list')
    else:
        # Initialize form with draft data
        form = ProjectProfileForm(initial=form_data, pre_selected_client_id=client.id)

    # Use the project_form.html template for both create and edit modes
    # Extract BOQ data from draft
    boq_data = []
    if 'boq_files' in draft_project.project_data:
        boq_files = draft_project.project_data['boq_files']
        if isinstance(boq_files, list):
            boq_data = boq_files
        elif isinstance(boq_files, str):
            # If it's a single file path, convert to list
            boq_data = [{'name': boq_files.split('/')[-1], 'path': boq_files}]
    
    context = {
        'form': form,
        'client': client,
        'project': draft_project,  # Pass the draft as project
        'is_edit': True,
        'is_draft': True,
        'edit_mode': True,  # Add this flag for template
        'source_label': SOURCE_LABELS.get(draft_project.project_source, draft_project.project_source),
        'project_type': draft_project.project_source,
        'next_id': draft_project.project_data.get('project_id'),
        'auto_fill_mode': False,
        'pre_selected_client': client,
        'show_client_selection': False,  # Don't show client selection in edit mode
        'boq_data': boq_data,  # Add BOQ data for edit mode
    }

    return render(request, "project_profiling/project_form.html", context)

@login_required
@verified_email_required
def delete_draft_project(request, draft_id):
    """Delete a draft project."""
    user_profile = get_object_or_404(UserProfile, user=request.user)

    draft_project = get_object_or_404(ProjectStaging,
                                     id=draft_id,
                                     created_by=user_profile,
                                     is_draft=True)

    if request.method == "POST":
        project_name = draft_project.project_data.get('project_name', 'Untitled')
        draft_project.delete()
        messages.success(request, f"Draft project '{project_name}' has been deleted.")

    return redirect('draft_projects_list')

@login_required
@verified_email_required
def review_pending_project(request, project_id):
    staging_id = project_id
    print("=== ENTERED review_staging_project VIEW ===")
    print(f"DEBUG: staging_id = {staging_id}")
    print(f"DEBUG: user = {request.user}, is_superuser = {request.user.is_superuser}")

    # --- Get user profile from session ---
    verified_profile = get_user_profile(request)
    print(f"DEBUG: verified_profile = {verified_profile}")
    if not verified_profile:
        print("DEBUG: Profile verification failed -> redirect unauthorized")
        return redirect("unauthorized")

    # --- Role check ---
    print(f"DEBUG: verified_profile.role = {getattr(verified_profile, 'role', None)}")
    if not (verified_profile.role == "EG" or request.user.is_superuser):
        print("DEBUG: Role check failed -> redirect unauthorized")
        messages.error(request, "You do not have permission to access this page.")
        return redirect("unauthorized")

    # --- Get staging project ---
    try:
        project = get_object_or_404(ProjectStaging, pk=staging_id)
        print(f"DEBUG: Loaded staging project ID={project.id}")
    except Exception as e:
        print(f"ERROR: Could not load ProjectStaging {staging_id} -> {e}")
        raise

    # --- Normalize project_data ---
    if isinstance(project.project_data, str):
        try:
            project.project_data = json.loads(project.project_data)
            print("DEBUG: Parsed project_data JSON successfully")
        except Exception as e:
            print(f"ERROR: Failed to parse project_data JSON -> {e}")
            project.project_data = {}

    # --- Get employee assignments from project_data (needed for context) ---
    employee_assignments = {}
    from employees.models import Employee

    # Map employee IDs to Employee objects
    employee_fields = [
        'project_in_charge', 'safety_officer', 'quality_assurance_officer',
        'quality_officer', 'foreman'
    ]

    for field in employee_fields:
        employee_id = project.project_data.get(field)
        if employee_id:
            try:
                employee = Employee.objects.get(id=employee_id)
                employee_assignments[field] = employee
                print(f"DEBUG: Loaded {field}: {employee.full_name}")
            except Employee.DoesNotExist:
                print(f"DEBUG: Employee with ID {employee_id} not found for {field}")
                employee_assignments[field] = None
        else:
            employee_assignments[field] = None

    # Handle project manager separately (it's stored differently)
    project_manager_id = project.project_data.get('project_manager_id')
    if project_manager_id:
        try:
            from authentication.models import UserProfile
            project_manager = UserProfile.objects.get(id=project_manager_id)
            employee_assignments['project_manager'] = project_manager
            print(f"DEBUG: Loaded project_manager: {project_manager.full_name}")
        except UserProfile.DoesNotExist:
            print(f"DEBUG: UserProfile with ID {project_manager_id} not found for project_manager")
            employee_assignments['project_manager'] = None
    else:
        employee_assignments['project_manager'] = None

    # Get number of laborers
    number_of_laborers = project.project_data.get('number_of_laborers', 0)
    print(f"DEBUG: Number of laborers: {number_of_laborers}")

    # --- Get client information ---
    client = None
    client_id = project.project_data.get("client") or project.project_data.get("client_id")
    if client_id:
        try:
            from manage_client.models import Client
            client = Client.objects.get(id=client_id)
            print(f"DEBUG: Loaded client: {client.company_name}")
        except Client.DoesNotExist:
            print(f"DEBUG: Client with ID {client_id} not found")

    # --- Get document URLs from old system ---
    contract_url = None
    permit_url = None

    # Check if documents are stored as file paths or URLs in project_data
    contract_agreement = project.project_data.get("contract_agreement")
    permits_licenses = project.project_data.get("permits_licenses")

    if contract_agreement:
        # If it's a file path, construct the media URL
        if hasattr(contract_agreement, 'url'):
            contract_url = contract_agreement.url
        elif isinstance(contract_agreement, str) and contract_agreement.startswith('/media/'):
            contract_url = contract_agreement
        elif isinstance(contract_agreement, str) and not contract_agreement.startswith('http'):
            contract_url = f"/media/{contract_agreement}" if not contract_agreement.startswith('/') else contract_agreement
        else:
            contract_url = contract_agreement

    if permits_licenses:
        # If it's a file path, construct the media URL
        if hasattr(permits_licenses, 'url'):
            permit_url = permits_licenses.url
        elif isinstance(permits_licenses, str) and permits_licenses.startswith('/media/'):
            permit_url = permits_licenses
        elif isinstance(permits_licenses, str) and not permits_licenses.startswith('http'):
            permit_url = f"/media/{permits_licenses}" if not permits_licenses.startswith('/') else permits_licenses
        else:
            permit_url = permits_licenses

    # --- Get documents from document library ---
    staging_documents = ProjectDocument.objects.filter(
        project_staging=project,
        is_archived=False
    ).order_by('-uploaded_at')
    print(f"DEBUG: Found {staging_documents.count()} document(s) from document library")

    # Prepare context
    context = {
        "project": project,
        "employee_assignments": employee_assignments,
        "number_of_laborers": number_of_laborers,
        "project_manager": employee_assignments.get('project_manager'),
        "client": client,
        "contract_url": contract_url,
        "permit_url": permit_url,
        "staging_documents": staging_documents,
    }

    # --- POST: Approve / Reject ---
    if request.method == "POST":
        action = request.POST.get("action")
        print(f"DEBUG: Received POST with action = {action}")

        if action == "approve_budget":
            try:
                # --- Get approved budget from form ---
                approved_budget = request.POST.get("approved_budget")
                if not approved_budget:
                    set_toast_message(request, "Please enter an approved budget amount.", "error")
                    return render(request, "project_profiling/review_pending_project.html", context)

                try:
                    approved_budget = float(approved_budget)
                    print(f"DEBUG: Approved budget: {approved_budget}")
                except ValueError:
                    set_toast_message(request, "Please enter a valid budget amount.", "error")
                    return render(request, "project_profiling/review_pending_project.html", context)

                # --- Get contract file from form ---
                contract_file = request.FILES.get("contract_file")
                if not contract_file:
                    set_toast_message(request, "Please upload a contract document.", "error")
                    return render(request, "project_profiling/review_pending_project.html", context)

                # --- Validate contract file ---
                allowed_types = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
                if contract_file.content_type not in allowed_types:
                    set_toast_message(request, "Please upload a PDF, DOC, or DOCX file.", "error")
                    return render(request, "project_profiling/review_pending_project.html", context)

                # Check file size (10MB limit)
                if contract_file.size > 10 * 1024 * 1024:
                    set_toast_message(request, "File size must be less than 10MB.", "error")
                    return render(request, "project_profiling/review_pending_project.html", context)

                # --- Get approval notes ---
                approval_notes = request.POST.get("approval_notes", "")

                # --- Budget validation ---
                estimated_cost = project.project_data.get("budget", 0) or project.project_data.get("estimated_cost", 0)
                if estimated_cost and estimated_cost > 0:
                    estimated_cost = float(estimated_cost)
                    
                    # Calculate minimum allowed budget (40% of estimated cost)
                    min_budget = estimated_cost * 0.4
                    
                    # Calculate maximum allowed budget (150% of estimated cost)
                    max_budget = estimated_cost * 1.5
                    
                    print(f"DEBUG: Budget validation - Estimated: {estimated_cost}, Min: {min_budget}, Max: {max_budget}, Approved: {approved_budget}")
                    
                    if approved_budget < min_budget:
                        set_toast_message(
                            request, 
                            f"❌ Approved budget (₱{approved_budget:,.2f}) is too low. "
                            f"Minimum allowed is ₱{min_budget:,.2f} (40% of estimated cost ₱{estimated_cost:,.2f}). "
                            f"Please increase the budget amount.",
                            "error"
                        )
                        return render(request, "project_profiling/review_pending_project.html", context)
                    
                    if approved_budget > max_budget:
                        set_toast_message(
                            request, 
                            f"⚠️ Approved budget (₱{approved_budget:,.2f}) is significantly higher than estimated cost. "
                            f"Maximum recommended is ₱{max_budget:,.2f} (150% of estimated cost ₱{estimated_cost:,.2f}). "
                            f"Please confirm this is correct before proceeding.",
                            "warning"
                        )
                        # Don't return here - allow override with warning

                # --- Get employee assignments, client, and project type ---
                from employees.models import Employee
                from authentication.models import UserProfile
                from manage_client.models import Client
                from .models import ProjectType

                # Get client object from ID
                client = None
                if project.project_data.get("client_id"):
                    try:
                        client = Client.objects.get(id=project.project_data.get("client_id"))
                        print(f"DEBUG: Found client: {client.company_name}")
                    except Client.DoesNotExist:
                        print(f"DEBUG: Client with ID {project.project_data.get('client_id')} not found")

                # Get or create project type
                project_type_instance = None
                project_type_name = project.project_data.get("project_type")
                if project_type_name:
                    project_type_instance, created = ProjectType.objects.get_or_create(
                        name=str(project_type_name),
                        defaults={
                            "description": f"Auto-created project type for {project_type_name}",
                            "created_by": project.created_by,
                        }
                    )
                    print(f"DEBUG: Project type: {project_type_instance.name} (created: {created})")

                # Handle date fields
                from datetime import datetime

                def parse_date(date_string):
                    if not date_string:
                        return None
                    if isinstance(date_string, str):
                        try:
                            return datetime.fromisoformat(date_string.replace('Z', '+00:00')).date()
                        except:
                            try:
                                return datetime.strptime(date_string, '%Y-%m-%d').date()
                            except:
                                print(f"DEBUG: Could not parse date: {date_string}")
                                return None
                    return date_string

                start_date = parse_date(project.project_data.get("start_date"))
                end_date = parse_date(project.project_data.get("end_date"))
                target_completion_date = parse_date(project.project_data.get("target_completion_date"))

                # Get employee objects from IDs
                project_in_charge = None
                safety_officer = None
                quality_assurance_officer = None
                quality_officer = None
                foreman = None
                project_manager = None

                if project.project_data.get("project_in_charge"):
                    try:
                        project_in_charge = Employee.objects.get(id=project.project_data.get("project_in_charge"))
                    except Employee.DoesNotExist:
                        print(f"DEBUG: Employee with ID {project.project_data.get('project_in_charge')} not found for project_in_charge")

                if project.project_data.get("safety_officer"):
                    try:
                        safety_officer = Employee.objects.get(id=project.project_data.get("safety_officer"))
                    except Employee.DoesNotExist:
                        print(f"DEBUG: Employee with ID {project.project_data.get('safety_officer')} not found for safety_officer")

                if project.project_data.get("quality_assurance_officer"):
                    try:
                        quality_assurance_officer = Employee.objects.get(id=project.project_data.get("quality_assurance_officer"))
                    except Employee.DoesNotExist:
                        print(f"DEBUG: Employee with ID {project.project_data.get('quality_assurance_officer')} not found for quality_assurance_officer")

                if project.project_data.get("quality_officer"):
                    try:
                        quality_officer = Employee.objects.get(id=project.project_data.get("quality_officer"))
                    except Employee.DoesNotExist:
                        print(f"DEBUG: Employee with ID {project.project_data.get('quality_officer')} not found for quality_officer")

                if project.project_data.get("foreman"):
                    try:
                        foreman = Employee.objects.get(id=project.project_data.get("foreman"))
                    except Employee.DoesNotExist:
                        print(f"DEBUG: Employee with ID {project.project_data.get('foreman')} not found for foreman")

                if project.project_data.get("project_manager_id"):
                    try:
                        project_manager = UserProfile.objects.get(id=project.project_data.get("project_manager_id"))
                    except UserProfile.DoesNotExist:
                        print(f"DEBUG: UserProfile with ID {project.project_data.get('project_manager_id')} not found for project_manager")

                # --- Create approved project ---
                new_profile = ProjectProfile.objects.create(
                    project_name=project.project_data.get("project_name", "Untitled Project"),
                    project_type=project_type_instance,
                    project_category=project.project_data.get("project_category"),
                    location=project.project_data.get("location"),
                    client=client,
                    # Use the correct field names for ProjectProfile
                    estimated_cost=project.project_data.get("budget", 0) or project.project_data.get("estimated_cost", 0),
                    approved_budget=approved_budget,
                    start_date=start_date,
                    target_completion_date=target_completion_date,
                    status="PL",  # Use "PL" for Planned instead of "Not Started"
                    project_source=project.project_source,
                    created_by=project.created_by,
                    # Employee assignments
                    project_in_charge=project_in_charge,
                    safety_officer=safety_officer,
                    quality_assurance_officer=quality_assurance_officer,
                    quality_officer=quality_officer,
                    foreman=foreman,
                    project_manager=project_manager,
                    number_of_laborers=project.project_data.get("number_of_laborers", 0),
                    # Additional fields that might be in project_data
                    site_engineer=project.project_data.get("site_engineer"),
                    city_province=project.project_data.get("city_province"),
                    gps_coordinates=project.project_data.get("gps_coordinates"),
                    description=project.project_data.get("description"),
                    subcontractors=project.project_data.get("subcontractors"),
                    payment_terms=project.project_data.get("payment_terms"),
                    # BOQ related fields
                    lot_size=project.project_data.get("lot_size", 0),
                )
                print(f"DEBUG: Created new ProjectProfile ID={new_profile.id}")

                # --- Save contract file ---
                if contract_file:
                    # Generate a unique filename
                    import os
                    from django.utils import timezone
                    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
                    file_extension = os.path.splitext(contract_file.name)[1]
                    filename = f"contract_{new_profile.project_id}_{timestamp}{file_extension}"
                    
                    # Save the file to the project's contract_agreement field
                    new_profile.contract_agreement.save(filename, contract_file, save=True)
                    print(f"DEBUG: Saved contract file: {filename}")

                # --- Copy permit file from staging project ---
                permits_licenses = project.project_data.get("permits_licenses")
                if permits_licenses:
                    try:
                        # Copy the permit file from staging to approved project
                        new_profile.permits_licenses = permits_licenses
                        new_profile.save()
                        print(f"DEBUG: Copied permit file from staging project")
                    except Exception as e:
                        print(f"DEBUG: Error copying permit file: {e}")

                # --- Save approval notes if provided ---
                if approval_notes:
                    # Store approval notes in a new field (we'll add this to the model)
                    # For now, we'll store it in the description or create a separate notes field
                    # Since ProjectProfile doesn't have project_data, we'll skip this for now
                    # TODO: Add approval_notes field to ProjectProfile model
                    print(f"DEBUG: Approval notes received: {approval_notes}")
                    print(f"DEBUG: Approved by: {request.user.userprofile.full_name}")
                    print(f"DEBUG: Approved at: {timezone.now().isoformat()}")

                # --- Migrate documents from staging project to approved project ---
                documents_to_migrate = ProjectDocument.objects.filter(project_staging=project)
                migrated_count = 0
                for doc in documents_to_migrate:
                    doc.project = new_profile
                    doc.project_staging = None
                    doc.save()
                    migrated_count += 1
                print(f"DEBUG: Migrated {migrated_count} document(s) from staging to approved project")

                # --- Create ProjectDocument entries for old system files ---
                # Create document entry for contract agreement if it exists
                if new_profile.contract_agreement:
                    try:
                        # Check if document entry already exists
                        existing_contract_doc = ProjectDocument.objects.filter(
                            project=new_profile,
                            document_type='CONTRACT'
                        ).first()
                        
                        if not existing_contract_doc:
                            # Create new document entry for contract
                            contract_doc = ProjectDocument.objects.create(
                                title='Contract Agreement',
                                description=f'Contract agreement for {new_profile.project_name}',
                                document_type='CONTRACT',
                                project_stage='INIT',
                                version='1.0',
                                file=new_profile.contract_agreement,
                                file_size=new_profile.contract_agreement.size,
                                uploaded_by=request.user.userprofile,
                                project=new_profile
                            )
                            print(f"DEBUG: Created ProjectDocument entry for contract: {contract_doc.id}")
                        else:
                            print(f"DEBUG: Contract document entry already exists: {existing_contract_doc.id}")
                    except Exception as e:
                        print(f"DEBUG: Error creating contract document entry: {e}")

                # Create document entry for permits if they exist
                if new_profile.permits_licenses:
                    try:
                        # Check if document entry already exists
                        existing_permit_doc = ProjectDocument.objects.filter(
                            project=new_profile,
                            document_type='PERMIT'
                        ).first()
                        
                        if not existing_permit_doc:
                            # Create new document entry for permits
                            permit_doc = ProjectDocument.objects.create(
                                title='Permits & Licenses',
                                description=f'Permits and licenses for {new_profile.project_name}',
                                document_type='PERMIT',
                                project_stage='INIT',
                                version='1.0',
                                file=new_profile.permits_licenses,
                                file_size=new_profile.permits_licenses.size,
                                uploaded_by=request.user.userprofile,
                                project=new_profile
                            )
                            print(f"DEBUG: Created ProjectDocument entry for permits: {permit_doc.id}")
                        else:
                            print(f"DEBUG: Permit document entry already exists: {existing_permit_doc.id}")
                    except Exception as e:
                        print(f"DEBUG: Error creating permit document entry: {e}")

                # --- Handle BOQ data and create budget entries ---
                boq_items = project.project_data.get('boq_items', [])
                boq_items_processed = False
                if boq_items:
                    try:
                        # Save BOQ data to the approved project
                        new_profile.boq_items = boq_items
                        new_profile.boq_file_processed = True
                        new_profile.extracted_total_cost = sum(float(item.get('total_cost', 0)) for item in boq_items)
                        
                        # Create cost breakdown
                        cost_breakdown = {
                            'materials': sum(float(item.get('material_cost', 0)) for item in boq_items),
                            'labor': sum(float(item.get('labor_cost', 0)) for item in boq_items),
                            'equipment': sum(float(item.get('equipment_cost', 0)) for item in boq_items),
                            'subcontractor': sum(float(item.get('subcontractor_cost', 0)) for item in boq_items),
                        }
                        new_profile.extracted_cost_breakdown = cost_breakdown
                        new_profile.save()
                        
                        # Create project scopes and budget entries from BOQ data
                        create_project_scopes_and_budgets_from_boq(new_profile, boq_items)
                        boq_items_processed = True
                        print(f"DEBUG: Created scopes and budget entries from BOQ data for approved project")
                        
                    except Exception as e:
                        print(f"DEBUG: Error handling BOQ data for approved project: {e}")
                        set_toast_message(request, f"⚠️ Project approved successfully, but there was an issue processing BOQ data: {str(e)}", "warning")

                # --- Handle contract file ---
                contract_path = project.project_data.get("contract_agreement")
                print(f"DEBUG: contract_path = {contract_path}")
                if contract_path and default_storage.exists(contract_path):
                    with default_storage.open(contract_path, "rb") as f:
                        new_profile.contract_agreement.save(os.path.basename(contract_path), File(f), save=True)
                    print("DEBUG: Contract agreement file copied")

                # --- Contribute to cost learning database ---
                try:
                    from .cost_learning import CostLearningEngine
                    contributed = CostLearningEngine.approve_project_costs(new_profile)
                    if contributed:
                        print(f"DEBUG: Project cost data contributed to learning database")
                except Exception as e:
                    print(f"DEBUG: Error contributing to cost learning: {e}")

                # --- Create notifications ---
                from notifications.models import Notification, NotificationStatus
                oms = UserProfile.objects.filter(role="OM")
                print(f"DEBUG: Found {oms.count()} OMs")
                if oms.exists():
                    # Create the notification
                    notif = Notification.objects.create(
                        message=f"A new project '{new_profile.project_name}' has been approved.",
                        link=f"/projects/{new_profile.pk}/details/",
                        role="OM",  # Target OMs
                    )
                    print(f"DEBUG: Notification created ID={notif.id}")

                    # Create notification status for each OM
                    for om in oms:
                        NotificationStatus.objects.create(
                            notification=notif,
                            user=om,
                            is_read=False,
                            cleared=False
                        )
                        print(f"DEBUG: Notification status created for OM: {om.full_name}")

                # --- Delete staging project ---
                project.delete()
                print("DEBUG: Deleted staging project after approval")

                # Short success message
                success_msg = f"🎉 Project '{new_profile.project_name}' approved successfully!"
                
                set_toast_message(request, success_msg, "success")
                
                # Redirect to appropriate project list based on project source
                if new_profile.project_source == "GC":
                    return redirect("project_list_general_contractor")
                else:
                    return redirect("project_list_direct_client")

            except Exception as e:
                print(f"ERROR during approve flow -> {e}")
                import traceback
                traceback.print_exc()
                set_toast_message(request, f"❌ Critical error occurred while approving the project: {str(e)}. Please try again or contact support.", "error")

        elif action == "reject":
            print("DEBUG: Reject action triggered")
            project_name = project.project_data.get('project_name', 'Untitled')
            project_id = project.project_data.get('project_id', 'N/A')
            project_source = project.project_source
            project.delete()
            print("DEBUG: Deleted staging project after rejection")
            set_toast_message(request, f"⚠️ Project '{project_name}' (ID: {project_id}) has been rejected and removed from the system.", "warning")
            
            # Redirect to appropriate project list based on project source
            if project_source == "GC":
                return redirect("project_list_general_contractor")
            else:
                return redirect("project_list_direct_client")

        else:
            print("DEBUG: Unknown action received")

    # --- Render template ---
    print("DEBUG: Rendering template with project data")
    return render(request, "project_profiling/review_pending_project.html", context)




SOURCE_LABELS = {
    "GC": "General Contractor",
    "DC": "Direct Client",
}

def serialize_field(value):
    """Convert unserializable types (date, decimal, files, etc.) into JSON-safe format for staging."""
    if value is None:
        return None

    # Dates
    if isinstance(value, (date, datetime)):
        return value.isoformat()

    # Decimals
    if isinstance(value, Decimal):
        return float(value)

    # UserProfile (custom)
    if hasattr(value, 'full_name') and hasattr(value, 'id'):
        return value.id  # store ID, not full_name

    # Client (custom)
    if isinstance(value, Client):
        return {
            "id": value.id,
            "company_name": value.company_name,
            "contact_name": value.contact_name,
        }

    # Choice fields (with .name)
    if hasattr(value, 'name') and not hasattr(value, 'read'):
        return str(value.name)

    # FileField / ImageField (store relative path)
    if hasattr(value, 'url') and hasattr(value, 'name'):
        return value.name  # e.g. "contracts/file.pdf"

    # UploadedFile objects (during POST)
    if hasattr(value, 'read') and hasattr(value, 'name'):
        return value.name

    return value


def create_project_budgets_from_boq(project_staging, boq_items):
    """
    Store BOQ items in project_data for later processing when project is approved.
    Since ProjectScope requires a project FK and we're dealing with staging projects,
    we'll store the BOQ data in project_data instead of creating separate budget entries.
    """
    
    # Store BOQ items in project_data for later processing
    if not hasattr(project_staging, 'project_data') or project_staging.project_data is None:
        project_staging.project_data = {}
    
    # Add BOQ data to project_data
    project_staging.project_data['boq_items'] = boq_items
    project_staging.project_data['boq_processed'] = True
    project_staging.project_data['boq_total_cost'] = sum(float(item.get('total_cost', 0)) for item in boq_items)
    
    # Calculate cost breakdown by category
    cost_breakdown = {
        'materials': sum(float(item.get('material_cost', 0)) for item in boq_items),
        'labor': sum(float(item.get('labor_cost', 0)) for item in boq_items),
        'equipment': sum(float(item.get('equipment_cost', 0)) for item in boq_items),
        'subcontractor': sum(float(item.get('subcontractor_cost', 0)) for item in boq_items),
    }
    project_staging.project_data['boq_cost_breakdown'] = cost_breakdown
    
    # Save the updated project_data
    project_staging.save()
    
    print(f"DEBUG: Stored {len(boq_items)} BOQ items in project_data with total cost: {project_staging.project_data['boq_total_cost']}")


def create_project_scopes_and_budgets_from_boq(project_profile, boq_items):
    """
    Create actual ProjectScope and ProjectBudget entries from BOQ items for approved projects.
    This function automatically scans all BOQ items, counts duplicates by section, 
    and distributes percentages to make 100%.
    """
    from scheduling.models import ProjectScope
    from .models import ProjectBudget
    
    print(f"DEBUG: Processing {len(boq_items)} BOQ items for project {project_profile.id}")
    
    # Step 1: Scan all BOQ items and group by section
    section_analysis = {}
    total_project_cost = 0
    
    for item in boq_items:
        section_name = item.get('section', 'General Items').strip()
        item_cost = float(item.get('total_cost', 0))
        total_project_cost += item_cost
        
        print(f"DEBUG: Item '{item.get('description', '')}' -> Section: '{section_name}', Cost: {item_cost}")
        
        if section_name not in section_analysis:
            section_analysis[section_name] = {
                'items': [],
                'total_cost': 0,
                'item_count': 0
            }
        
        section_analysis[section_name]['items'].append(item)
        section_analysis[section_name]['total_cost'] += item_cost
        section_analysis[section_name]['item_count'] += 1
    
    print(f"DEBUG: Section Analysis Complete:")
    print(f"DEBUG: Total Project Cost: {total_project_cost}")
    print(f"DEBUG: Found {len(section_analysis)} distinct sections:")
    
    # Step 2: Calculate weights and ensure they sum to 100%
    section_weights = {}
    weight_sum = 0
    
    for section_name, data in section_analysis.items():
        # Calculate percentage based on cost
        raw_weight = (data['total_cost'] / total_project_cost) * 100 if total_project_cost > 0 else 0
        section_weights[section_name] = raw_weight
        weight_sum += raw_weight
        
        print(f"DEBUG: '{section_name}': {data['item_count']} items, ₱{data['total_cost']:,.2f} ({raw_weight:.2f}%)")
    
    # Step 3: Normalize weights to ensure they sum to exactly 100%
    if weight_sum > 0:
        normalization_factor = 100 / weight_sum
        section_names = list(section_weights.keys())
        
        # First pass: normalize and round to 2 decimal places
        for section_name in section_names:
            section_weights[section_name] = round(section_weights[section_name] * normalization_factor, 2)
        
        # Second pass: adjust for rounding errors to ensure exact 100% sum
        current_sum = sum(section_weights.values())
        difference = 100.0 - current_sum
        
        if abs(difference) > 0.01:  # Only adjust if difference is significant
            # Add the difference to the largest weight to maintain exact 100%
            largest_section = max(section_weights.keys(), key=lambda k: section_weights[k])
            section_weights[largest_section] = round(section_weights[largest_section] + difference, 2)
    
    print(f"DEBUG: Normalized weights (should sum to 100%): {sum(section_weights.values()):.2f}%")
    
    # Step 4: Create scopes and budget entries
    created_scopes = []
    
    for section_name, data in section_analysis.items():
        try:
            final_weight = section_weights.get(section_name, 0)
            
            print(f"DEBUG: Creating scope '{section_name}' with weight {final_weight}%")
            
            # Create ProjectScope
            scope, created = ProjectScope.objects.get_or_create(
                project=project_profile,
                name=section_name,
                defaults={
                    'weight': final_weight
                }
            )
            
            if created:
                created_scopes.append(section_name)
                print(f"DEBUG: ✓ Created new scope '{section_name}' with ID {scope.id}")
            else:
                print(f"DEBUG: ⚠ Scope '{section_name}' already exists, updating weight to {final_weight}%")
                scope.weight = final_weight
                scope.save()
            
            # Create budget entries for each item in this section
            # Group items by category to avoid duplicate scope-category combinations
            category_totals = {}
            
            for item in data['items']:
                try:
                    item_cost = float(item.get('total_cost', 0))
                    if item_cost > 0:
                        # Determine category based on item data - fix string/int comparison
                        category = 'MAT'  # Default to Materials
                        material_cost = float(item.get('material_cost', 0))
                        labor_cost = float(item.get('labor_cost', 0))
                        equipment_cost = float(item.get('equipment_cost', 0))
                        subcontractor_cost = float(item.get('subcontractor_cost', 0))
                        
                        if material_cost > 0:
                            category = 'MAT'
                        elif labor_cost > 0:
                            category = 'LAB'
                        elif equipment_cost > 0:
                            category = 'EQU'
                        elif subcontractor_cost > 0:
                            category = 'SUB'
                        
                        # Accumulate costs by category for this scope
                        if category not in category_totals:
                            category_totals[category] = 0
                        category_totals[category] += item_cost
                        
                        print(f"DEBUG: ✓ Processed BOQ item '{item.get('description', '')}' (₱{item_cost:,.2f}) -> Category: {category}")
                        
                except Exception as item_error:
                    print(f"DEBUG: Error processing BOQ item '{item.get('description', '')}': {item_error}")
                    continue
            
            # Create one budget entry per category per scope
            for category, total_amount in category_totals.items():
                try:
                    budget_entry, created = ProjectBudget.objects.get_or_create(
                        project=project_profile,
                        scope=scope,
                        category=category,
                        defaults={
                            'planned_amount': total_amount
                        }
                    )
                    
                    if created:
                        print(f"DEBUG: ✓ Created budget entry for scope '{scope.name}' - {category}: ₱{total_amount:,.2f}")
                    else:
                        # Update existing entry
                        budget_entry.planned_amount = total_amount
                        budget_entry.save()
                        print(f"DEBUG: ✓ Updated budget entry for scope '{scope.name}' - {category}: ₱{total_amount:,.2f}")
                        
                except Exception as budget_error:
                    print(f"DEBUG: Error creating budget entry for scope '{scope.name}' - {category}: {budget_error}")
                    continue
            
        except Exception as scope_error:
            print(f"DEBUG: Error creating scope '{section_name}': {scope_error}")
            continue
    
    print(f"DEBUG: SUCCESS! Created {len(created_scopes)} new scopes: {created_scopes}")
    print(f"DEBUG: Total scopes in project: {ProjectScope.objects.filter(project=project_profile).count()}")
    print(f"DEBUG: Total budget entries created: {ProjectBudget.objects.filter(project=project_profile).count()}")


@login_required
@verified_email_required
@role_required('EG', 'OM')
def project_create(request, project_type, client_id):
    """Create a new project - all projects go to staging for approval."""
    print(f"DEBUG: project_create called with project_type={project_type}, client_id={client_id}")
    print(f"DEBUG: request.method={request.method}")
    print(f"DEBUG: request.POST={dict(request.POST)}")
    print(f"DEBUG: request.FILES={dict(request.FILES)}")
    
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    # Import Client model at the top level
    from manage_client.models import Client
    
    # Handle case when client_id is 'new' (from floating button)
    if client_id == 'new':
        # Get all active clients for the dropdown
        clients = Client.objects.filter(is_active=True, client_type=project_type).order_by('company_name')
        
        if request.method == 'POST':
            # Get selected client ID from form
            selected_client_id = request.POST.get('client')
            print(f"DEBUG: selected_client_id from form = {selected_client_id}")
            print(f"DEBUG: all POST data = {dict(request.POST)}")
            if not selected_client_id:
                print("DEBUG: No client selected, showing error message")
                messages.error(request, "Please select a client before creating the project.")
                FormClass = get_project_form_class(project_type)
                form = FormClass(request.POST, request.FILES)
                return render(request, "project_profiling/project_form.html", {
                    "form": form,
                    "project_type": project_type,
                    "source_label": SOURCE_LABELS.get(project_type, "Unknown"),
                    "next_id": get_next_project_id(project_type),
                    "clients": clients,
                    "auto_fill_mode": False,
                    "show_client_selection": True,
                })
            
            # Process the form submission directly instead of redirecting
            # Get the client and continue with normal project creation flow
            client = get_object_or_404(Client, id=selected_client_id)
            print(f"DEBUG: Client retrieved: {client.company_name} (ID: {client.id})")
            
            # Continue with the normal project creation flow below
            # (This will fall through to the existing project creation logic)
        
        elif request.method == 'GET':
            # GET request - show form with client selection
            next_id = get_next_project_id(project_type)
            FormClass = get_project_form_class(project_type)
            form = FormClass()
            
            return render(request, "project_profiling/project_form.html", {
                "form": form,
                "project_type": project_type,
                "source_label": SOURCE_LABELS.get(project_type, "Unknown"),
                "next_id": next_id,
                "clients": clients,
                "auto_fill_mode": False,
                "show_client_selection": True,
            })

    # Get client - either from the 'new' flow or directly from client_id
    if client_id != 'new':
        client = get_object_or_404(Client, id=client_id)
    
    FormClass = ProjectProfileForm
    initial_source = project_type

    # --- Generate Next Project ID ---
    last_project = ProjectProfile.objects.filter(project_source=project_type).aggregate(Max("project_id"))
    last_id = last_project["project_id__max"]
    if last_id:
        try:
            prefix = project_type
            number = int(str(last_id).replace(f"{prefix}-", ""))
            next_id = f"{prefix}-{number+1:03d}"
        except Exception:
            next_id = f"{project_type}-001"
    else:
        next_id = f"{project_type}-001"

    if request.method == "POST":
        print(f"DEBUG: POST data keys: {list(request.POST.keys())}")
        print(f"DEBUG: POST files keys: {list(request.FILES.keys())}")
        
        # Debug BOQ data specifically
        boq_items_data = request.POST.get('boq_items')
        print(f"DEBUG: BOQ items data: {boq_items_data[:200] if boq_items_data else 'None'}...")
        
        # Check if this is a draft save
        is_draft_save = request.POST.get('save_as_draft') == 'true'
        is_ajax = (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
                  'application/json' in request.headers.get('Accept', ''))
        
        print(f"DEBUG: is_draft_save = {is_draft_save}")
        print(f"DEBUG: is_ajax = {is_ajax}")
        print(f"DEBUG: X-Requested-With header = {request.headers.get('X-Requested-With')}")
        print(f"DEBUG: Accept header = {request.headers.get('Accept')}")
        print(f"DEBUG: POST data keys = {list(request.POST.keys())}")
        print(f"DEBUG: save_as_draft value = {request.POST.get('save_as_draft')}")
        
        # Create form first - use the actual client ID, not the URL parameter
        # Handle case where client might not be set yet (for 'new' flow)
        if client_id == 'new' and 'client' in request.POST:
            # Get client from form data
            selected_client_id = request.POST.get('client')
            if selected_client_id:
                client = get_object_or_404(Client, id=selected_client_id)
                print(f"DEBUG: Client set from form data: {client.company_name} (ID: {client.id})")
        
        actual_client_id = client.id if hasattr(client, 'id') else client_id
        print(f"DEBUG: Using client_id for form: {actual_client_id}")
        form = FormClass(request.POST, request.FILES, pre_selected_client_id=actual_client_id)
        
        # For draft saves, handle differently - BEFORE form validation
        if is_draft_save:
            print(f"DEBUG: Processing draft save for project_type={project_type}, client_id={client_id}")
            print(f"DEBUG: About to process draft save...")
            print(f"DEBUG: Client object: {client}")
            print(f"DEBUG: Client ID: {client.id if hasattr(client, 'id') else 'No ID'}")
            try:
                # Save as draft even with incomplete data
                cleaned_data = {}
                for key, value in request.POST.items():
                    if key not in ['csrfmiddlewaretoken', 'save_as_draft']:
                        cleaned_data[key] = value
                
                # Handle file uploads for drafts
                for key, file in request.FILES.items():
                    if hasattr(file, "read") and hasattr(file, "name"):
                        file_path = default_storage.save(f"drafts/{key}/{file.name}", file)
                        cleaned_data[key] = file_path
                
                # Create a unique draft identifier based on session and client
                draft_key = f"draft_{verified_profile.id}_{client.id}_{project_type}"

                # Find existing draft for this specific user, client, and project type
                existing_draft = ProjectStaging.objects.filter(
                    created_by=verified_profile,
                    project_source=project_type,
                    is_draft=True,
                ).first()

                # Check if the existing draft is for the same client
                if existing_draft and str(existing_draft.project_data.get('client_id')) == str(client.id):
                    # Update existing draft
                    existing_draft.project_data = {
                        **cleaned_data,
                        'project_id': next_id,
                        'client_id': client.id,
                        'draft_key': draft_key,
                    }
                    existing_draft.submitted_at = timezone.now()
                    existing_draft.save()
                    project = existing_draft
                    created = False
                else:
                    # Create new draft only if no existing draft for this client
                    project = ProjectStaging.objects.create(
                        created_by=verified_profile,
                        project_source=project_type,
                        is_draft=True,
                        project_data={
                            **cleaned_data,
                            'project_id': next_id,
                            'client_id': client.id,
                            'draft_key': draft_key,
                        },
                        submitted_at=timezone.now(),
                        submitted_for_approval=False,
                    )
                    created = True
                
                return JsonResponse({
                    'success': True, 
                    'message': f'💾 Draft "{cleaned_data.get("project_name", "Project")}" saved successfully!',
                    'project_id': project.id,
                    'details': {
                        'project_name': cleaned_data.get('project_name'),
                        'project_id': next_id,
                        'saved_at': timezone.now().isoformat()
                    }
                })
                
            except Exception as e:
                print(f"DEBUG: Error saving draft: {e}")
                return JsonResponse({
                    'success': False, 
                    'error': f'❌ Failed to save draft: {str(e)}',
                    'details': {
                        'error_type': type(e).__name__,
                        'timestamp': timezone.now().isoformat()
                    }
                })
        else:
            # For draft saves, we want to be more lenient with validation
            if is_draft_save:
                # Remove required validation for draft saves
                for field in form.fields.values():
                    field.required = False
            else:
                print(f"DEBUG: Creating regular form (not draft)")
                print(f"DEBUG: Regular form created, checking validity...")
            
            # Regular form submission (not draft)
            print(f"DEBUG: About to check form validity...")
            if form.is_valid():
                print(f"DEBUG: Form is valid, processing data...")
                try:
                    cleaned_data = {}
                    for k, v in form.cleaned_data.items():
                        if hasattr(v, "read") and hasattr(v, "name"):
                            file_path = default_storage.save(f"{k}/{v.name}", v)
                            cleaned_data[k] = file_path
                        else:
                            cleaned_data[k] = serialize_field(v)
                    
                    # Handle BOQ data from hidden form field
                    boq_items_data = request.POST.get('boq_items')
                    if boq_items_data:
                        try:
                            import json
                            boq_items = json.loads(boq_items_data)
                            cleaned_data['boq_items'] = boq_items
                            cleaned_data['boq_file_processed'] = True
                            
                            # Calculate total cost from BOQ items
                            total_cost = sum(float(item.get('total_cost', 0)) for item in boq_items)
                            cleaned_data['extracted_total_cost'] = total_cost
                            
                            # Create cost breakdown
                            cost_breakdown = {
                                'materials': sum(float(item.get('material_cost', 0)) for item in boq_items),
                                'labor': sum(float(item.get('labor_cost', 0)) for item in boq_items),
                                'equipment': sum(float(item.get('equipment_cost', 0)) for item in boq_items),
                                'subcontractor': sum(float(item.get('subcontractor_cost', 0)) for item in boq_items),
                            }
                            cleaned_data['extracted_cost_breakdown'] = cost_breakdown
                            
                            # Update the project's estimated cost with BOQ total
                            if 'estimated_cost' in cleaned_data:
                                cleaned_data['estimated_cost'] = total_cost
                            else:
                                cleaned_data['estimated_cost'] = total_cost
                            
                            # Debug: Print BOQ data being saved
                            print(f"DEBUG: Saving BOQ data - {len(boq_items)} items, Total cost: {total_cost}")
                            
                        except json.JSONDecodeError as e:
                            print(f"DEBUG: JSON decode error in BOQ data: {e}")
                            messages.error(request, f"❌ Invalid BOQ data format. Please re-upload your BOQ file.")
                            return render(request, "project_profiling/project_form.html", {"form": form, "client": client, "project_type": project_type})
                        except ValueError as e:
                            print(f"DEBUG: Value error in BOQ data: {e}")
                            messages.error(request, f"❌ Invalid BOQ data values. Please check your BOQ file format.")
                            return render(request, "project_profiling/project_form.html", {"form": form, "client": client, "project_type": project_type})
                        except Exception as e:
                            print(f"DEBUG: Unexpected error processing BOQ data: {e}")
                            messages.error(request, f"❌ Error processing BOQ data: {str(e)}. Please try again or contact support.")
                            return render(request, "project_profiling/project_form.html", {"form": form, "client": client, "project_type": project_type})
                    else:
                        print("DEBUG: No BOQ data found in form submission")
                    
                    # Handle BOQ file uploads (simple file storage approach)
                    boq_files = request.FILES.getlist('boq_files')
                    if boq_files:
                        boq_file_paths = []
                        for boq_file in boq_files:
                            # Save BOQ file
                            file_path = default_storage.save(f"boq_files/{boq_file.name}", boq_file)
                            boq_file_paths.append(file_path)
                        cleaned_data['boq_file_paths'] = boq_file_paths
                        print(f"DEBUG: Saved BOQ files: {boq_file_paths}")

                    # Use the next project ID that was already generated at the beginning of the function

                    # Get related instances
                    project_manager_id = cleaned_data.get("project_manager")
                    project_manager_instance = UserProfile.objects.filter(id=project_manager_id).first() if project_manager_id else None
                    
                    # Get client instance - use the client we retrieved earlier if not in cleaned_data
                    client_id_from_form = cleaned_data.get("client")
                    if client_id_from_form:
                        client_instance = Client.objects.filter(id=client_id_from_form).first()
                    else:
                        # Fall back to the client we retrieved earlier
                        client_instance = client
                        print(f"DEBUG: Using fallback client: {client_instance.company_name if client_instance else 'None'} (ID: {client_instance.id if client_instance else 'None'})")

                    # Check if there's an existing draft to convert
                    draft_session = request.session.get('draft_session')
                    existing_draft = None

                    if draft_session:
                        try:
                            existing_draft = ProjectStaging.objects.get(
                                id=draft_session,
                                created_by=verified_profile,
                                is_draft=True
                            )
                            print(f"DEBUG: Found existing draft: {existing_draft.id}")
                        except ProjectStaging.DoesNotExist:
                            print("DEBUG: Draft session exists but draft not found, creating new one")
                            existing_draft = None

                    # Update existing draft or create new staging project
                    if existing_draft:
                        existing_draft.project_data = {
                            **{k: serialize_field(v) for k, v in cleaned_data.items()},
                            "project_manager_id": project_manager_instance.id if project_manager_instance else None,
                            "client_id": client_instance.id if client_instance else None,
                            "project_id": next_id,
                        }
                        existing_draft.submitted_at = timezone.now()
                        existing_draft.save()
                        project = existing_draft

                        # Clear the draft session
                        if 'draft_session' in request.session:
                            del request.session['draft_session']
                    else:
                        # Create final project (not draft)
                        project = ProjectStaging.objects.create(
                            created_by=verified_profile,
                            project_source=project_type,
                            is_draft=False,  # This is a final submission
                            submitted_for_approval=True,  # Ready for approval
                            project_data={
                                **{k: serialize_field(v) for k, v in cleaned_data.items()},
                                "project_manager_id": project_manager_instance.id if project_manager_instance else None,
                                "client_id": client_instance.id if client_instance else None,
                                "project_id": next_id,
                            },
                            submitted_at=timezone.now(),
                        )

                    # Create project budget entries from BOQ data if available
                    boq_processed = False
                    if cleaned_data.get('boq_items'):
                        try:
                            create_project_budgets_from_boq(project, cleaned_data['boq_items'])
                            boq_processed = True
                            print(f"DEBUG: Created budget entries from BOQ data")
                        except Exception as e:
                            print(f"DEBUG: Error creating budget entries: {e}")
                            messages.warning(request, f"⚠️ Project created successfully, but there was an issue processing BOQ budget data: {str(e)}")

                    # Notify the creator
                    notif_self = Notification.objects.create(
                        message=f"You created the project '{cleaned_data.get('project_name', 'Unnamed')}'. It has been saved in pending projects awaiting approval.",
                        link=reverse(
                            "project_list_direct_client" if project_type == "DC" else "project_list_general_contractor"
                        )
                    )
                    NotificationStatus.objects.create(notification=notif_self, user=verified_profile)

                    # Shortened success message
                    project_name = cleaned_data.get('project_name', 'Unnamed')
                    success_msg = f"Project '{project_name}' created successfully! ID: {next_id}"
                    
                    # Use toast system for better user feedback
                    set_toast_message(request, success_msg, 'success', 8000)
                    redirect_url = "project_list_general_contractor" if project_type == "GC" else "project_list_direct_client"
                    return redirect(redirect_url)
                    
                except Exception as e:
                    print(f"DEBUG: Critical error during project creation: {e}")
                    import traceback
                    traceback.print_exc()
                    messages.error(request, f"❌ Critical error occurred while creating the project: {str(e)}. Please try again or contact support.")
                    return render(request, "project_profiling/project_form.html", {"form": form, "client": client, "project_type": project_type})
                
            else:
                print(f"DEBUG: Form validation failed!")
                print(f"DEBUG: Form errors: {form.errors}")
                print(f"DEBUG: Form non_field_errors: {form.non_field_errors()}")
                for field, errors in form.errors.items():
                    print(f"DEBUG: Field '{field}' errors: {errors}")
                
                # Add specific error messages for each field with better formatting
                error_count = 0
                error_messages = []
                for field, errors in form.errors.items():
                    field_display = field.replace('_', ' ').title()
                    for error in errors:
                        error_count += 1
                        error_messages.append(f"❌ {field_display}: {error}")
                
                # Add summary error message
                if error_count > 0:
                    summary_msg = f"⚠️ Form validation failed with {error_count} error(s). Please correct the highlighted fields and try again."
                    error_messages.append(summary_msg)
                else:
                    error_messages.append("❌ There were errors in your form. Please check and try again.")
                
                # Use toast system for error feedback
                set_toast_message(request, error_messages[0], 'error', 10000)
                return render(request, "project_profiling/project_form.html", {"form": form, "client": client, "project_type": project_type})

    else:
        # Check if there's an existing draft for this user and project type
        existing_draft = ProjectStaging.objects.filter(
            created_by=verified_profile,
            project_source=project_type,
            is_draft=True
        ).first()
        
        initial_data = {
            "project_source": initial_source,
            "project_id": next_id,
        }
        
        # Load draft data if exists
        if existing_draft:
            draft_data = existing_draft.project_data
            initial_data.update(draft_data)
            messages.info(request, "Draft data loaded. You can continue editing your project.")
        else:
            # Auto-fill payment terms based on client type
            if client.client_type == 'GC':
                initial_data["payment_terms"] = "Net 30 days"
            elif client.client_type == 'DC':
                initial_data["payment_terms"] = "Net 15 days"
                
            # Auto-select first available project type for this client
            client_project_types = client.project_types.filter(is_active=True)
            if client_project_types.exists():
                initial_data["project_type"] = client_project_types.first()

        form = FormClass(initial=initial_data, pre_selected_client_id=client_id)

    # Fallback: If this is a draft save request but we haven't handled it yet, return JSON error
    if request.method == 'POST' and request.POST.get('save_as_draft') == 'true':
        print("DEBUG: Fallback - Draft save not handled properly, returning JSON error")
        return JsonResponse({
            'success': False,
            'error': '❌ Draft save failed: Request not processed correctly',
            'details': {
                'error_type': 'ProcessingError',
                'timestamp': timezone.now().isoformat()
            }
        }, status=500)

    return render(request, "project_profiling/project_form.html", {
        "form": form,
        "project_type": initial_source,
        "source_label": SOURCE_LABELS.get(initial_source, "Unknown"),
        "next_id": next_id,
        "pre_selected_client": client,
        "auto_fill_mode": True,
    })


def project_drafts(request):
    """List user's draft projects."""
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")
    
    drafts = ProjectStaging.objects.filter(
        created_by=verified_profile,
        is_draft=True
    ).order_by('-submitted_at')
    
    return render(request, 'project_profiling/project_drafts.html', {
        'drafts': drafts,
        'role': verified_profile.role
    })
    
@verified_email_required
@role_required('EG', 'OM')
def project_edit_signed_with_role(request, pk):
    """Edit an existing approved project."""
    print("DEBUG: project_edit_signed_with_role called")
    print(f"DEBUG: Method={request.method}, ProjectID={pk}")

    verified_profile = get_user_profile(request)
    if not verified_profile:
        print("DEBUG: Profile verification failed -> redirect unauthorized")
        return redirect("unauthorized")

    print(f"DEBUG: Verified profile -> {verified_profile}")

    project = get_object_or_404(ProjectProfile, id=pk)
    print(f"DEBUG: Loaded project -> {project}")

    FormClass = ProjectProfileForm

    if request.method == "POST":
        print("DEBUG: Handling POST submission")
        form = FormClass(request.POST, request.FILES, instance=project)
        print(f"DEBUG: Form is valid? {form.is_valid()}")

        if form.is_valid():
            updated_project = form.save(commit=False)

            contract_file = request.FILES.get("contract_agreement")
            if contract_file:
                print(f"DEBUG: New contract file uploaded -> {contract_file.name}")
                updated_project.contract_agreement.save(
                    contract_file.name, contract_file, save=False
                )

            permits_file = request.FILES.get("permits_licenses")
            if permits_file:
                print(f"DEBUG: New permits file uploaded -> {permits_file.name}")
                updated_project.permits_licenses.save(
                    permits_file.name, permits_file, save=False
                )

            updated_project.save()
            print(f"DEBUG: Project updated -> ID={updated_project.id}")
            messages.success(request, f"Project '{project.project_name}' updated successfully.")
            return redirect(
                "project_view",
                project_source=project.project_source,
                pk=project.id,
            )
        else:
            print(f"DEBUG: Form errors -> {form.errors}")
            messages.error(request, "There were errors in your form. Please check and try again.")
    else:
        print("DEBUG: GET request -> rendering edit form")
        form = FormClass(instance=project)

    return render(request, "project_profiling/project_edit.html", {
        "form": form,
        "project_type": project.project_source,
        "project": project,
        "source_label": SOURCE_LABELS.get(project.project_source, "Unknown"),
    })


@login_required
@verified_email_required
@role_required('EG', 'OM')
def project_archive_signed_with_role(request, project_type, pk):
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    # --- Fetch project ---
    if request.user.is_superuser or verified_profile.role in ['EG', 'OM']:
        # Superusers, Engineers, and Operations Managers can access any project
        project = get_object_or_404(ProjectProfile, pk=pk)
    else:  # PM (Project Manager) can only access their own projects
        project = get_object_or_404(
            ProjectProfile.objects.filter(
                Q(created_by=verified_profile) |
                Q(project_manager=verified_profile),
                pk=pk
            )
        )

    # --- Handle archive action ---
    if request.method == 'POST':
        project.archived = True
        project.save()
        messages.success(request, "Project archived successfully.")

        if project.project_source == "GC":
            return redirect("project_list_general_contractor")
        else:
            return redirect("project_list_direct_client")

    return render(request, 'project_profiling/project_confirm_archieve.html', {
        'project': project,
        'project_type': project_type,
    })

    

# ----------------------------------------------
# PROJECTS BUDGET 
# ----------------------------------------------

@login_required
@verified_email_required
@role_required('EG', 'OM')
def approve_budget(request, project_id):
    project = get_object_or_404(ProjectProfile, id=project_id)

    if request.method == 'POST':
        approved_budget = request.POST.get('approved_budget')
        if approved_budget:
            try:
                project.approved_budget = float(approved_budget)
                project.save()

                # Contribute to cost learning database if project has BOQ data
                try:
                    from .cost_learning import CostLearningEngine
                    contributed = CostLearningEngine.approve_project_costs(project)
                    if contributed:
                        messages.info(
                            request,
                            'Project cost data has been added to the cost learning database.'
                        )
                except Exception as e:
                    print(f"DEBUG: Error contributing to cost learning: {e}")

                set_toast_message(
                    request,
                    f'Budget of ₱{float(approved_budget):,.2f} approved successfully! '
                    f'You can now proceed with budget planning.',
                    "success"
                )
                return redirect('budget_planning', project_id=project_id)
            except ValueError:
                set_toast_message(request, 'Invalid budget amount entered.', "error")

    return redirect('project_detail', project_id=project_id)


@login_required
@verified_email_required
@role_required("EG", "OM")
def budget_planning(request, project_id):
    """
    Main budget planning interface - this is where users define categories
    after budget approval
    """
    project = get_object_or_404(ProjectProfile, id=project_id)
    project_scopes = project.scopes.all()
    
    # Check if budget is approved
    if not project.approved_budget:
        set_toast_message(request, "Budget must be approved before planning can begin.", "warning")
        return redirect('project_detail', project_id=project_id)
    
    # Get all budget categories for this project - INCLUDE category_other field
    budgets = project.budgets.select_related('scope').all().order_by('scope__name', 'category')
    
    # Get all scopes for this project
    project_scopes = project.scopes.all()
    
    # Calculate totals
    total_planned = budgets.aggregate(total=Sum("planned_amount"))["total"] or 0
    remaining_budget = project.approved_budget - total_planned
    
    # Group budgets by scope for better display
    scopes_data = {}
    for scope in project_scopes:
        scope_budgets = budgets.filter(scope=scope)
        scope_total = scope_budgets.aggregate(total=Sum("planned_amount"))["total"] or 0
        
        scopes_data[scope.name] = {
            'scope': scope,
            'categories': scope_budgets,  # This now includes category_other
            'total': scope_total
        }

    if request.method == "POST":
        form = ProjectBudgetForm(request.POST, project=project)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.project = project
            
            # Handle category_other field
            if budget.category == 'OTH' and form.cleaned_data.get('category_other'):
                budget.category_other = form.cleaned_data['category_other']
            else:
                budget.category_other = None  # Clear if not "Other"
            
            # Check if total would exceed approved budget (but allow it)
            new_total = total_planned + budget.planned_amount
            if new_total > project.approved_budget:
                budget.save()
                messages.warning(request, f"Budget added successfully, but total planned (₱{new_total:,.2f}) exceeds approved budget (₱{project.approved_budget:,.2f}) by ₱{new_total - project.approved_budget:,.2f}")
                return redirect("budget_planning", project_id=project.id)
            else:
                budget.save()
                messages.success(request, f"Budget for {budget.scope.name} - {budget.get_category_display()} added successfully. Remaining budget: ₱{project.approved_budget - new_total:,.2f}")
                return redirect("budget_planning", project_id=project.id)
        else:
            messages.error(request, "There was an error adding the budget. Please check the form.")
    else:
        form = ProjectBudgetForm(project=project)

    return render(request, "budgets/budget_planning.html", {
        "project": project,
        "budgets": budgets,
        "scopes": scopes_data,
        "project_scopes": project_scopes,
        "form": form,
        "total_planned": total_planned,
        "remaining_budget": remaining_budget,
        "budget_utilization": (total_planned / project.approved_budget * 100) if project.approved_budget > 0 else 0,
    })

@login_required
@verified_email_required
@role_required("EG", "OM")
@require_http_methods(["POST"])
def edit_budget_ajax(request, project_id, budget_id):
    """
    AJAX endpoint for editing budget amounts
    """
    try:
        # Get the project and budget
        project = get_object_or_404(ProjectProfile, id=project_id)
        budget = get_object_or_404(ProjectBudget, id=budget_id, project=project)
        
        # Parse JSON data from request
        data = json.loads(request.body)
        planned_amount = data.get('planned_amount')
        
        # Validate the planned amount
        if not planned_amount:
            return JsonResponse({'error': 'Planned amount is required'}, status=400)
        
        try:
            planned_amount = float(planned_amount)
            if planned_amount < 0:
                return JsonResponse({'error': 'Planned amount cannot be negative'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid planned amount format'}, status=400)
        
        # Check if the change would exceed approved budget
        other_budgets_total = project.budgets.exclude(id=budget_id).aggregate(
            total=Sum("planned_amount")
        )["total"] or 0
        new_total = float(other_budgets_total) + planned_amount
        
        if new_total > float(project.approved_budget):
            return JsonResponse({
                'error': f'This change would exceed the approved budget of ₱{project.approved_budget:,.2f}. '
                        f'Current total would be ₱{new_total:,.2f}'
            }, status=400)
        
        # Store old amount and convert to float
        old_amount = float(budget.planned_amount)
        
        # Update the budget
        budget.planned_amount = planned_amount
        budget.save()
        
        # Return success response - all calculations now use floats
        return JsonResponse({
            'success': True,
            'message': 'Budget updated successfully',
            'old_amount': old_amount,
            'new_amount': planned_amount,
            'change': planned_amount - old_amount,
            'total_planned': new_total,
            'remaining_budget': float(project.approved_budget) - new_total
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

@login_required
@verified_email_required
@role_required("EG", "OM")
def delete_budget(request, project_id, budget_id):
    project = get_object_or_404(ProjectProfile, id=project_id)
    budget = get_object_or_404(ProjectBudget, id=budget_id, project=project)

    if request.method == "POST":
        # Check if there are any allocations
        allocation_count = budget.allocations.count()
        if allocation_count > 0:
            messages.warning(request, f"Cannot delete budget with {allocation_count} existing allocations. Remove allocations first.")
            return redirect("budget_planning", project_id=project.id)
        
        scope_category = f"{budget.scope.name} - {budget.get_category_display()}"
        budget.delete()
        messages.success(request, f"Budget entry '{scope_category}' deleted successfully.")
        return redirect("budget_planning", project_id=project.id)

    return render(request, "project_profiling/confirm_delete_budget.html", {
        "project": project,
        "budget": budget,
    })

# ----------------------------------------
# PROJECTS ALLOCATION
# ----------------------------------------    

@login_required
@verified_email_required
@role_required("EG", "OM")
def allocate_fund_to_category(request, project_id, budget_id):
    project = get_object_or_404(ProjectProfile, id=project_id)
    budget = get_object_or_404(ProjectBudget, id=budget_id, project=project)
    
    if request.method == "POST":
        amount_str = request.POST.get("amount")
        note = request.POST.get("note", "")
        
        if not amount_str:
            messages.error(request, "Please enter an allocation amount.")
        else:
            try:
                amount = Decimal(amount_str)
                if amount <= 0:
                    messages.error(request, "Amount must be greater than zero.")
                elif amount > 9999999999999.99: 
                    messages.error(request, "Amount exceeds the maximum allowed (₱9,999,999,999,999.99).")
                else:
                    FundAllocation.objects.create(
                        project_budget=budget,
                        amount=amount,
                        note=note
                    )
                    messages.success(
                        request, 
                        f"₱{amount:,.2f} allocated to {budget.get_category_display()} successfully."
                    )
                    return redirect("allocate_fund_to_category", project_id=project.id, budget_id=budget.id)
            except InvalidOperation:
                messages.error(request, "Invalid amount entered. Please enter a valid number.")

    # Get active allocations (not soft deleted)
    all_allocations = budget.allocations.filter(is_deleted=False).order_by('-date_allocated')
    
    # Get soft-deleted allocations for restore functionality
    deleted_allocations = budget.allocations.filter(is_deleted=True).order_by('-deleted_at')
    
    # Sum of all non-deleted allocations for this category
    total_allocated = all_allocations.aggregate(total=models.Sum("amount"))["total"] or 0
    remaining = budget.planned_amount - total_allocated
    remaining_abs = abs(remaining)

    # Calculate allocation percentage for progress bar
    if budget.planned_amount > 0:
        allocation_percent = min((total_allocated / budget.planned_amount) * 100, 100)
    else:
        allocation_percent = 0

    # Pagination for active allocations
    paginator = Paginator(all_allocations, 10)
    page = request.GET.get('page', 1)

    try:
        allocations = paginator.page(page)
    except PageNotAnInteger:
        allocations = paginator.page(1)
    except EmptyPage:
        allocations = paginator.page(paginator.num_pages)

    return render(request, "budgets/allocate_fund_category.html", {
        "project": project,
        "budget": budget,
        "total_allocated": total_allocated,
        "remaining": remaining,
        "remaining_abs": remaining_abs,      
        "allocation_percent": allocation_percent,
        "allocations": allocations,
        "deleted_allocations": deleted_allocations,
        "total_allocations": all_allocations.count(),
    })

@require_POST 
def soft_delete_allocation(request, project_id, budget_id, allocation_id):
    """Soft delete an allocation"""
    project = get_object_or_404(ProjectProfile, id=project_id)
    budget = get_object_or_404(ProjectBudget, id=budget_id, project=project)
    allocation = get_object_or_404(
        FundAllocation, 
        id=allocation_id, 
        project_budget=budget,
        is_deleted=False
    )
    
    allocation.soft_delete()
    return JsonResponse({
        'status': 'success', 
        'message': 'Allocation soft deleted successfully',
        'allocation_id': allocation_id
    })

@require_POST
def hard_delete_allocation(request, project_id, budget_id, allocation_id):
    """Hard delete an allocation"""
    project = get_object_or_404(ProjectProfile, id=project_id)
    budget = get_object_or_404(ProjectBudget, id=budget_id, project=project)
    allocation = get_object_or_404(
        FundAllocation, 
        id=allocation_id, 
        project_budget=budget
    )
    
    allocation.delete()  # Permanently delete
    return JsonResponse({
        'status': 'success', 
        'message': 'Allocation permanently deleted',
        'allocation_id': allocation_id
    })

@require_POST
def restore_allocation(request, project_id, budget_id, allocation_id):
    """Restore a soft-deleted allocation"""
    project = get_object_or_404(ProjectProfile, id=project_id)
    budget = get_object_or_404(ProjectBudget, id=budget_id, project=project)
    allocation = get_object_or_404(
        FundAllocation, 
        id=allocation_id, 
        project_budget=budget,
        is_deleted=True  # Only restore soft-deleted items
    )
    
    allocation.restore()
    return JsonResponse({
        'status': 'success', 
        'message': 'Allocation restored successfully',
        'allocation_id': allocation_id
    })
    
    
@login_required
@verified_email_required
@role_required("EG", "OM")    
def project_allocate_budget(request, project_id):
    """
    Overview of all budget categories for allocation
    """
    project = get_object_or_404(ProjectProfile, id=project_id)
    budgets = project.budgets.all().order_by('scope__name', 'category')
    
    # Calculate allocation summary for each budget
    budget_summary = []
    for budget in budgets:
        total_allocated = budget.allocations.aggregate(total=models.Sum("amount"))["total"] or 0
        remaining = budget.planned_amount - total_allocated
        allocation_percent = (total_allocated / budget.planned_amount * 100) if budget.planned_amount > 0 else 0
        
        budget_summary.append({
            'budget': budget,
            'total_allocated': total_allocated,
            'remaining': remaining,
            'allocation_percent': allocation_percent,
            'status': 'over' if remaining < 0 else 'complete' if remaining == 0 else 'partial'
        })
    
    return render(request, "budgets/allocate_funds_overview.html", {
        "project": project,
        "budget_summary": budget_summary,
    })
    
@require_http_methods(["POST"])
def delete_scope(request, project_id):
    """
    Delete or soft-delete a project scope
    """
    try:
        project = get_object_or_404(ProjectProfile, id=project_id)
        data = json.loads(request.body)
        scope_id = data.get('scope_id')
        force_delete = data.get('force_delete', False)
        
        scope = get_object_or_404(ProjectScope, id=scope_id, project=project)
        
        # Check if scope has associated tasks
        has_tasks = scope.tasks.exists()  # Assuming you have a related name 'tasks'
        
        if has_tasks and force_delete:
            return JsonResponse({
                'error': 'Cannot permanently delete scope with associated tasks. Use soft delete instead.'
            }, status=400)
        
        if has_tasks:
            # Soft delete - mark as deleted but keep data
            scope.is_deleted = True
            scope.save()
            message = f"Scope '{scope.name}' has been soft deleted (hidden but preserved for existing tasks)."
        else:
            # Hard delete - actually remove the scope and related data
            scope_name = scope.name
            
            # Delete related budget categories first
            scope.budget_categories.all().delete()
            
            # Delete the scope
            scope.delete()
            message = f"Scope '{scope_name}' has been permanently deleted."
        
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'An error occurred: {str(e)}'
        }, status=500)

@require_http_methods(["POST"])
def restore_scope(request, project_id):
    """
    Restore a soft-deleted project scope
    """
    try:
        project = get_object_or_404(ProjectProfile, id=project_id)
        data = json.loads(request.body)
        scope_id = data.get('scope_id')
        
        scope = get_object_or_404(ProjectScope, id=scope_id, project=project)
        
        if not scope.is_deleted:
            return JsonResponse({
                'error': 'Scope is not deleted and cannot be restored.'
            }, status=400)
        
        scope.is_deleted = False
        scope.save()
        
        return JsonResponse({
            'success': True,
            'message': f"Scope '{scope.name}' has been restored successfully."
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'An error occurred: {str(e)}'
        }, status=500)
        
@require_http_methods(["POST"])
def edit_scope(request, project_id, scope_id):
    """Edit a project scope"""
    try:
        project = get_object_or_404(ProjectProfile, id=project_id)
        scope = get_object_or_404(ProjectScope, id=scope_id, project=project)
        data = json.loads(request.body)
        
        name = data.get('name', '').strip()
        weight = data.get('weight')
        
        if not name:
            return JsonResponse({'error': 'Scope name is required.'}, status=400)
        
        try:
            weight = float(weight)
            if weight <= 0 or weight > 100:
                return JsonResponse({'error': 'Weight must be between 0.01 and 100.'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid weight value.'}, status=400)
        
        # Check if name already exists for this project (excluding current scope)
        if project.scopes.filter(name=name).exclude(id=scope_id).exists():
            return JsonResponse({'error': f'A scope with name "{name}" already exists.'}, status=400)
        
        scope.name = name
        scope.weight = weight
        scope.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Scope "{name}" updated successfully.'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
    
def add_expense(request, project_id):
    if request.method == 'POST':
        try:
            project = get_object_or_404(ProjectProfile, id=project_id)
            category = get_object_or_404(ProjectBudget, id=request.POST['category_id'])
            
            # Check if there's any allocation for this category - use Decimal
            total_allocated = category.allocations.filter(
                is_deleted=False
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
            
            if total_allocated == 0:
                return JsonResponse({
                    'error': 'No allocation found for this category. Please allocate funds first.'
                })
            
            # Calculate current spent amount - use Decimal
            total_spent = category.expenses.aggregate(
                total=models.Sum('amount')
            )['total'] or Decimal('0')
            
            expense_amount = Decimal(str(request.POST['amount']))  # Convert to Decimal
            new_total_spent = total_spent + expense_amount
            
            # Warning if over-allocation (but still allow)
            warning = ""
            if new_total_spent > total_allocated:
                overage = new_total_spent - total_allocated
                warning = f" (Over-allocated by ₱{overage:,.2f})"
            
            expense = Expense.objects.create(
                project=project,
                budget_category=category,
                expense_type=request.POST['expense_type'],
                expense_other=request.POST.get('expense_other', ''),
                amount=expense_amount,
                vendor=request.POST.get('vendor', ''),
                receipt_number=request.POST.get('receipt_number', ''),
                expense_date=request.POST['expense_date'],
                description=request.POST.get('description', ''),
                created_by=request.user.userprofile  # Fixed this line
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Expense of ₱{expense.amount:,.2f} added successfully{warning}'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)})
    
    return JsonResponse({'error': 'Invalid request method'})

def get_category_allocation(request, project_id, category_id):
    print(f"DEBUG: Starting with project_id={project_id}, category_id={category_id}")
    
    try:
        # Step 1: Check if project exists
        project = get_object_or_404(ProjectProfile, id=project_id)
        print(f"DEBUG: Found project: {project.project_name} (id: {project.id})")
        
        # Step 2: Check if category exists (without project filter)
        try:
            category = ProjectBudget.objects.get(id=category_id)
            print(f"DEBUG: Found category: {category.get_category_display()}")
            print(f"DEBUG: Category scope: {category.scope.name}")
            print(f"DEBUG: Category scope project: {category.scope.project.project_name} (id: {category.scope.project.id})")
            print(f"DEBUG: Project match? {category.scope.project.id == project.id}")
            
            # Step 3: Check if the category belongs to the right project
            if category.scope.project.id != project.id:
                return JsonResponse({
                    'error': f'Category belongs to project {category.scope.project.project_name}, not {project.project_name}',
                    'allocated_amount': 0,
                    'spent_amount': 0,
                    'remaining_amount': 0
                })
                
        except ProjectBudget.DoesNotExist:
            return JsonResponse({
                'error': f'No ProjectBudget with id {category_id} exists',
                'allocated_amount': 0,
                'spent_amount': 0,
                'remaining_amount': 0
            })
        
        # Step 4: Get allocations and expenses with proper Decimal handling
        allocations = category.allocations.filter(is_deleted=False)
        print(f"DEBUG: Found {allocations.count()} allocations")
        
        # Use Decimal(0) instead of 0 for proper type consistency
        total_allocated = allocations.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        
        print(f"DEBUG: Total allocated: {total_allocated} (type: {type(total_allocated)})")
        
        expenses = category.expenses.all()
        print(f"DEBUG: Found {expenses.count()} expenses")
        
        total_spent = expenses.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        
        print(f"DEBUG: Total spent: {total_spent} (type: {type(total_spent)})")
        
        # Calculate remaining (both are now Decimal types)
        remaining_amount = total_allocated - total_spent
        print(f"DEBUG: Remaining: {remaining_amount} (type: {type(remaining_amount)})")
        
        return JsonResponse({
            'allocated_amount': float(total_allocated),
            'spent_amount': float(total_spent),
            'remaining_amount': float(remaining_amount),
            'category_name': category.get_category_display(),
            'debug': f"Allocations: {allocations.count()}, Expenses: {expenses.count()}"
        })
        
    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': str(e),
            'allocated_amount': 0,
            'spent_amount': 0,
            'remaining_amount': 0
        })

# ----------------------------------------
# DOCUMENT LIBRARY
# ----------------------------------------

@login_required
@verified_email_required
def document_library(request):
    """Main document library view"""
    return render(request, 'project_profiling/document_library.html')

@login_required
@require_http_methods(["GET"])
def api_document_stats(request):
    """Get document statistics"""
    try:
        user_profile = request.user.userprofile

        # Filter documents based on user role
        if user_profile.role in ['EG', 'OM']:
            documents = ProjectDocument.objects.all()
        elif user_profile.role == 'PM':
            documents = ProjectDocument.objects.filter(
                Q(project__project_manager=user_profile) |
                Q(project_staging__created_by=user_profile)
            )
        else:
            documents = ProjectDocument.objects.none()

        # Calculate stats
        total_documents = documents.count()
        contracts = documents.filter(document_type='CONTRACT').count()
        reports = documents.filter(document_type='REPORT').count()

        # Calculate total size
        total_size_bytes = documents.aggregate(
            total=Sum('file_size')
        )['total'] or 0

        # Add old system documents to stats
        from .models import ProjectProfile
        
        # Get old system documents based on user role
        if user_profile.role in ['EG', 'OM']:
            old_projects = ProjectProfile.objects.filter(
                Q(contract_agreement__isnull=False) | Q(permits_licenses__isnull=False)
            ).exclude(
                Q(contract_agreement='') | Q(permits_licenses='')
            )
        elif user_profile.role == 'PM':
            old_projects = ProjectProfile.objects.filter(
                Q(contract_agreement__isnull=False) | Q(permits_licenses__isnull=False)
            ).exclude(
                Q(contract_agreement='') | Q(permits_licenses='')
            ).filter(project_manager=user_profile)
        else:
            old_projects = ProjectProfile.objects.none()

        # Count old system documents
        old_contracts = old_projects.filter(contract_agreement__isnull=False).exclude(contract_agreement='').count()
        old_permits = old_projects.filter(permits_licenses__isnull=False).exclude(permits_licenses='').count()
        
        # Update totals
        total_documents += old_contracts + old_permits
        contracts += old_contracts

        # Convert to MB
        total_size_mb = total_size_bytes / (1024 * 1024)
        if total_size_mb >= 1000:
            total_size = f"{total_size_mb / 1024:.1f} GB"
        else:
            total_size = f"{total_size_mb:.1f} MB"

        return JsonResponse({
            'total_documents': total_documents,
            'contracts': contracts,
            'reports': reports,
            'total_size': total_size
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def api_documents_list(request):
    """Get filtered list of documents"""
    try:
        user_profile = request.user.userprofile

        # Base queryset based on user role
        if user_profile.role in ['EG', 'OM']:
            documents = ProjectDocument.objects.select_related(
                'project', 'project_staging', 'uploaded_by', 'uploaded_by__user'
            ).all()
        elif user_profile.role == 'PM':
            # Include both approved projects and pending projects created by the PM
            documents = ProjectDocument.objects.select_related(
                'project', 'project_staging', 'uploaded_by', 'uploaded_by__user'
            ).filter(
                Q(project__project_manager=user_profile) |
                Q(project_staging__created_by=user_profile)
            )
        else:
            documents = ProjectDocument.objects.none()

        # Apply filters
        search = request.GET.get('search', '').strip()
        if search:
            documents = documents.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__icontains=search)
            )

        doc_type = request.GET.get('type', 'ALL')
        if doc_type and doc_type != 'ALL':
            documents = documents.filter(document_type=doc_type)

        stage = request.GET.get('stage', 'ALL')
        if stage and stage != 'ALL':
            documents = documents.filter(project_stage=stage)

        project_id = request.GET.get('project', '')
        if project_id:
            if project_id.startswith('pending_'):
                # Filter by pending project
                staging_id = int(project_id.replace('pending_', ''))
                documents = documents.filter(project_staging_id=staging_id)
            else:
                # Filter by approved project
                documents = documents.filter(project_id=project_id)

        # Filter archived documents
        show_archived = request.GET.get('show_archived', 'false').lower() == 'true'
        if not show_archived:
            documents = documents.filter(is_archived=False)

        # Order by most recent
        documents = documents.order_by('-uploaded_at')

        # Format response
        data = []
        for doc in documents:
            # Get file extension
            file_extension = ''
            if doc.file:
                file_extension = doc.file.name.split('.')[-1] if '.' in doc.file.name else ''

            # Format file size
            file_size = doc.file_size or 0
            if file_size >= 1024 * 1024:
                file_size_str = f"{file_size / (1024 * 1024):.1f} MB"
            elif file_size >= 1024:
                file_size_str = f"{file_size / 1024:.1f} KB"
            else:
                file_size_str = f"{file_size} Bytes"

            # Get project name from either project or project_staging
            if doc.project:
                project_name = doc.project.project_name
            elif doc.project_staging:
                project_name = f"{doc.project_staging.project_data.get('project_name', 'Unnamed')} (Pending)"
            else:
                project_name = 'N/A'

            data.append({
                'id': doc.id,
                'title': doc.title,
                'description': doc.description,
                'document_type': doc.document_type,
                'document_type_display': doc.get_document_type_display(),
                'project_stage': doc.project_stage,
                'project_stage_display': doc.get_project_stage_display(),
                'project_name': project_name,
                'version': doc.version,
                'file_size': file_size_str,
                'file_extension': file_extension,
                'uploaded_by': doc.uploaded_by.full_name if doc.uploaded_by else 'Unknown',
                'uploaded_at': localtime(doc.uploaded_at).strftime('%b %d, %Y %I:%M %p'),
                'tags': doc.tags or '',
                'is_archived': doc.is_archived
            })

        # Add old system documents (contracts and permits stored directly on projects)
        # Get projects that have contracts or permits
        from .models import ProjectProfile
        
        # Base queryset for projects based on user role
        if user_profile.role in ['EG', 'OM']:
            projects_with_docs = ProjectProfile.objects.filter(
                Q(contract_agreement__isnull=False) | Q(permits_licenses__isnull=False)
            ).exclude(
                Q(contract_agreement='') | Q(permits_licenses='')
            )
        elif user_profile.role == 'PM':
            projects_with_docs = ProjectProfile.objects.filter(
                Q(contract_agreement__isnull=False) | Q(permits_licenses__isnull=False)
            ).exclude(
                Q(contract_agreement='') | Q(permits_licenses='')
            ).filter(project_manager=user_profile)
        else:
            projects_with_docs = ProjectProfile.objects.none()

        # Apply project filter if specified
        if project_id and not project_id.startswith('pending_'):
            projects_with_docs = projects_with_docs.filter(id=project_id)

        # Add old system documents to the data
        for project in projects_with_docs:
            # Add contract agreement if exists
            if project.contract_agreement:
                file_size = project.contract_agreement.size if hasattr(project.contract_agreement, 'size') else 0
                if file_size >= 1024 * 1024:
                    file_size_str = f"{file_size / (1024 * 1024):.1f} MB"
                elif file_size >= 1024:
                    file_size_str = f"{file_size / 1024:.1f} KB"
                else:
                    file_size_str = f"{file_size} Bytes"

                file_extension = project.contract_agreement.name.split('.')[-1] if '.' in project.contract_agreement.name else ''

                data.append({
                    'id': f"old_contract_{project.id}",
                    'title': 'Contract Agreement',
                    'description': f'Contract agreement for {project.project_name}',
                    'document_type': 'CONTRACT',
                    'document_type_display': 'Contract',
                    'project_stage': 'INIT',
                    'project_stage_display': 'Initiation',
                    'project_name': project.project_name,
                    'version': '1.0',
                    'file_size': file_size_str,
                    'file_extension': file_extension,
                    'uploaded_by': project.project_manager.full_name if project.project_manager else 'System',
                    'uploaded_at': localtime(project.created_at).strftime('%b %d, %Y %I:%M %p'),
                    'tags': 'contract, agreement',
                    'is_archived': False,
                    'old_system': True,
                    'download_url': project.contract_agreement.url
                })

            # Add permits and licenses if exists
            if project.permits_licenses:
                file_size = project.permits_licenses.size if hasattr(project.permits_licenses, 'size') else 0
                if file_size >= 1024 * 1024:
                    file_size_str = f"{file_size / (1024 * 1024):.1f} MB"
                elif file_size >= 1024:
                    file_size_str = f"{file_size / 1024:.1f} KB"
                else:
                    file_size_str = f"{file_size} Bytes"

                file_extension = project.permits_licenses.name.split('.')[-1] if '.' in project.permits_licenses.name else ''

                data.append({
                    'id': f"old_permit_{project.id}",
                    'title': 'Permits & Licenses',
                    'description': f'Permits and licenses for {project.project_name}',
                    'document_type': 'PERMIT',
                    'document_type_display': 'Permit',
                    'project_stage': 'INIT',
                    'project_stage_display': 'Initiation',
                    'project_name': project.project_name,
                    'version': '1.0',
                    'file_size': file_size_str,
                    'file_extension': file_extension,
                    'uploaded_by': project.project_manager.full_name if project.project_manager else 'System',
                    'uploaded_at': localtime(project.created_at).strftime('%b %d, %Y %I:%M %p'),
                    'tags': 'permit, license',
                    'is_archived': False,
                    'old_system': True,
                    'download_url': project.permits_licenses.url
                })

        return JsonResponse({
            'documents': data,
            'count': len(data)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def api_document_detail(request, doc_id):
    """Get detailed information about a document"""
    try:
        user_profile = request.user.userprofile

        # Get document with permission check
        if user_profile.role in ['EG', 'OM']:
            document = get_object_or_404(
                ProjectDocument.objects.select_related('project', 'project_staging', 'uploaded_by', 'uploaded_by__user'),
                id=doc_id
            )
        elif user_profile.role == 'PM':
            document = get_object_or_404(
                ProjectDocument.objects.select_related('project', 'project_staging', 'uploaded_by', 'uploaded_by__user'),
                id=doc_id
            )
            # Verify PM has access
            if document.project and document.project.project_manager != user_profile:
                return JsonResponse({'error': 'Unauthorized'}, status=403)
            if document.project_staging and document.project_staging.created_by != user_profile:
                return JsonResponse({'error': 'Unauthorized'}, status=403)
        else:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        # Get file extension
        file_extension = ''
        if document.file:
            file_extension = document.file.name.split('.')[-1] if '.' in document.file.name else ''

        # Format file size
        file_size = document.file_size or 0
        if file_size >= 1024 * 1024:
            file_size_str = f"{file_size / (1024 * 1024):.1f} MB"
        elif file_size >= 1024:
            file_size_str = f"{file_size / 1024:.1f} KB"
        else:
            file_size_str = f"{file_size} Bytes"

        # Get project name from either project or project_staging
        if document.project:
            project_name = document.project.project_name
        elif document.project_staging:
            project_name = f"{document.project_staging.project_data.get('project_name', 'Unnamed')} (Pending)"
        else:
            project_name = 'N/A'

        data = {
            'id': document.id,
            'title': document.title,
            'description': document.description,
            'document_type': document.document_type,
            'document_type_display': document.get_document_type_display(),
            'project_stage': document.project_stage,
            'project_stage_display': document.get_project_stage_display(),
            'project_name': project_name,
            'version': document.version,
            'file_size': file_size_str,
            'file_extension': file_extension,
            'uploaded_by': document.uploaded_by.full_name if document.uploaded_by else 'Unknown',
            'uploaded_at': localtime(document.uploaded_at).strftime('%b %d, %Y %I:%M %p'),
            'tags': document.tags or ''
        }

        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def api_document_upload(request):
    """Upload a new document or multiple files with version tracking"""
    try:
        user_profile = request.user.userprofile

        # Check permissions
        if user_profile.role not in ['EG', 'OM', 'PM']:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        # Get form data
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        project_id = request.POST.get('project')
        document_type = request.POST.get('document_type')
        project_stage = request.POST.get('project_stage')
        version = request.POST.get('version', '1.0')
        version_notes = request.POST.get('version_notes', '').strip()
        tags = request.POST.get('tags', '').strip()
        replaces_id = request.POST.get('replaces_id')  # ID of document this version replaces

        # Support multiple files
        files = request.FILES.getlist('files')
        if not files:
            # Fallback to single file for backward compatibility
            single_file = request.FILES.get('file')
            if single_file:
                files = [single_file]

        # Validate required fields
        if not all([title, project_id, document_type, project_stage]) or not files:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Check if this is a pending project (ID starts with "pending_")
        project = None
        staging_project = None

        if project_id.startswith('pending_'):
            # Extract the staging ID
            try:
                staging_id = int(project_id.replace('pending_', ''))
                staging_project = get_object_or_404(ProjectStaging, id=staging_id)

                # Check if PM has access to this pending project
                if user_profile.role == 'PM' and staging_project.created_by != user_profile:
                    return JsonResponse({'error': 'Unauthorized for this project'}, status=403)
            except (ValueError, ProjectStaging.DoesNotExist):
                return JsonResponse({'error': 'Invalid pending project ID'}, status=400)
        else:
            # Get approved project
            project = get_object_or_404(ProjectProfile, id=project_id)

            # Check if PM has access to this project
            if user_profile.role == 'PM' and project.project_manager != user_profile:
                return JsonResponse({'error': 'Unauthorized for this project'}, status=403)

        # Get the document this version replaces (if specified)
        replaces_document = None
        if replaces_id:
            try:
                if project:
                    replaces_document = ProjectDocument.objects.get(
                        id=replaces_id,
                        project=project
                    )
                elif staging_project:
                    replaces_document = ProjectDocument.objects.get(
                        id=replaces_id,
                        project_staging=staging_project
                    )
            except ProjectDocument.DoesNotExist:
                pass

        # If no replaces_id but version > 1.0, try to find latest version by title
        if not replaces_document and version != '1.0':
            if project:
                replaces_document = ProjectDocument.objects.filter(
                    project=project,
                    title=title,
                    document_type=document_type,
                    is_archived=False
                ).order_by('-uploaded_at').first()
            elif staging_project:
                replaces_document = ProjectDocument.objects.filter(
                    project_staging=staging_project,
                    title=title,
                    document_type=document_type,
                    is_archived=False
                ).order_by('-uploaded_at').first()

        # Create documents
        uploaded_docs = []
        for file in files:
            document = ProjectDocument.objects.create(
                project=project,
                project_staging=staging_project,
                title=title if len(files) == 1 else f"{title} - {file.name}",
                description=description,
                document_type=document_type,
                project_stage=project_stage,
                file=file,
                version=version,
                version_notes=version_notes,
                replaces=replaces_document,  # Link to previous version
                tags=tags,
                uploaded_by=user_profile,
                file_size=file.size
            )
            uploaded_docs.append({
                'id': document.id,
                'title': document.title,
                'version': document.version
            })

        return JsonResponse({
            'success': True,
            'message': f'{len(uploaded_docs)} document(s) uploaded successfully',
            'documents': uploaded_docs
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def api_document_download(request, doc_id):
    """Download a document"""
    try:
        user_profile = request.user.userprofile

        # Get document with permission check
        if user_profile.role in ['EG', 'OM']:
            document = get_object_or_404(ProjectDocument, id=doc_id)
        elif user_profile.role == 'PM':
            # PM can access documents from their approved projects or pending projects they created
            document = get_object_or_404(
                ProjectDocument,
                id=doc_id
            )
            # Verify PM has access
            if document.project and document.project.project_manager != user_profile:
                return HttpResponse('Unauthorized', status=403)
            if document.project_staging and document.project_staging.created_by != user_profile:
                return HttpResponse('Unauthorized', status=403)
        else:
            return HttpResponse('Unauthorized', status=403)

        # Serve the file
        if document.file:
            response = HttpResponse(document.file.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(document.file.name)}"'
            return response
        else:
            return HttpResponse('File not found', status=404)

    except Exception as e:
        return HttpResponse(str(e), status=500)

@login_required
@require_http_methods(["GET"])
def api_document_versions(request, doc_id):
    """Get version history of a document"""
    try:
        user_profile = request.user.userprofile

        # Get document with permission check
        if user_profile.role in ['EG', 'OM']:
            document = get_object_or_404(ProjectDocument, id=doc_id)
        elif user_profile.role == 'PM':
            document = get_object_or_404(
                ProjectDocument,
                id=doc_id,
                project__project_manager=user_profile
            )
        else:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        # Get all previous versions
        versions = []
        current = document.replaces
        while current:
            versions.append({
                'id': current.id,
                'version': current.version,
                'description': current.description,
                'version_notes': current.version_notes or '',
                'uploaded_at': localtime(current.uploaded_at).strftime('%b %d, %Y %I:%M %p'),
                'uploaded_by': current.uploaded_by.full_name if current.uploaded_by else 'Unknown'
            })
            current = current.replaces

        return JsonResponse({'versions': versions})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def api_projects_list(request):
    """Get list of projects for dropdowns"""
    try:
        user_profile = request.user.userprofile

        # Get approved projects based on role
        if user_profile.role in ['EG', 'OM']:
            projects = ProjectProfile.objects.filter(archived=False).order_by('project_name')
        elif user_profile.role == 'PM':
            projects = ProjectProfile.objects.filter(
                project_manager=user_profile,
                archived=False
            ).order_by('project_name')
        else:
            projects = ProjectProfile.objects.none()

        data = [{
            'id': p.id,
            'project_id': p.project_id,
            'project_name': p.project_name,
            'status': 'approved'
        } for p in projects]

        # Add pending projects from ProjectStaging
        if user_profile.role in ['EG', 'OM']:
            # Get all pending projects (not drafts)
            pending_projects = ProjectStaging.objects.filter(
                status='PL',
                is_draft=False,
                submitted_for_approval=True
            ).order_by('-submitted_at')
        elif user_profile.role == 'PM':
            # PM can only see their pending projects
            pending_projects = ProjectStaging.objects.filter(
                status='PL',
                is_draft=False,
                submitted_for_approval=True,
                created_by=user_profile
            ).order_by('-submitted_at')
        else:
            pending_projects = ProjectStaging.objects.none()

        # Add pending projects to the data list
        for pending in pending_projects:
            project_name = pending.project_data.get('project_name', 'Unnamed Project')
            project_id = pending.project_data.get('project_id', pending.project_id_placeholder or 'N/A')
            
            data.append({
                'id': f"pending_{pending.id}",  # Prefix with 'pending_' to distinguish from approved projects
                'project_id': project_id,
                'project_name': f"{project_name} (Pending Approval)",
                'status': 'pending',
                'staging_id': pending.id  # Include staging ID for reference
            })

        return JsonResponse({'projects': data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def api_document_archive(request, doc_id):
    """Archive a document"""
    try:
        user_profile = request.user.userprofile

        # Check permissions
        if user_profile.role not in ['EG', 'OM', 'PM']:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        # Get document with permission check
        if user_profile.role in ['EG', 'OM']:
            document = get_object_or_404(ProjectDocument, id=doc_id)
        elif user_profile.role == 'PM':
            document = get_object_or_404(
                ProjectDocument,
                id=doc_id,
                project__project_manager=user_profile
            )
        else:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        # Archive the document
        document.is_archived = True
        document.save()

        return JsonResponse({
            'success': True,
            'message': f'Document "{document.title}" archived successfully'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def api_document_restore(request, doc_id):
    """Restore an archived document"""
    try:
        user_profile = request.user.userprofile

        # Check permissions
        if user_profile.role not in ['EG', 'OM', 'PM']:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        # Get document with permission check
        if user_profile.role in ['EG', 'OM']:
            document = get_object_or_404(ProjectDocument, id=doc_id)
        elif user_profile.role == 'PM':
            document = get_object_or_404(
                ProjectDocument,
                id=doc_id,
                project__project_manager=user_profile
            )
        else:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        # Restore the document
        document.is_archived = False
        document.save()

        return JsonResponse({
            'success': True,
            'message': f'Document "{document.title}" restored successfully'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def clear_toast_session(request):
    """Clear the toast session data after displaying it"""
    if request.method == 'POST':
        if 'show_toast' in request.session:
            del request.session['show_toast']
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
@require_GET
def reverse_geocode(request):
    """
    Proxy endpoint for reverse geocoding using Nominatim API.
    This avoids CORS issues when calling the API from the frontend.
    """
    try:
        # Get parameters from the request
        lat = request.GET.get('lat')
        lon = request.GET.get('lon')
        zoom = request.GET.get('zoom', '18')
        addressdetails = request.GET.get('addressdetails', '1')
        countrycodes = request.GET.get('countrycodes', 'ph')
        
        if not lat or not lon:
            return JsonResponse({
                'error': 'Latitude and longitude are required'
            }, status=400)
        
        # Build the Nominatim API URL
        nominatim_url = 'https://nominatim.openstreetmap.org/reverse'
        params = {
            'format': 'json',
            'lat': lat,
            'lon': lon,
            'zoom': zoom,
            'addressdetails': addressdetails,
            'countrycodes': countrycodes,
        }
        
        # Add User-Agent header as required by Nominatim
        headers = {
            'User-Agent': 'PowerMason/1.0 (Project Management System)'
        }
        
        # Make the request to Nominatim
        response = requests.get(nominatim_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the response
        data = response.json()
        
        # Return the data with proper CORS headers
        json_response = JsonResponse(data)
        json_response['Access-Control-Allow-Origin'] = '*'
        json_response['Access-Control-Allow-Methods'] = 'GET'
        json_response['Access-Control-Allow-Headers'] = 'Content-Type'
        
        return json_response
        
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'error': f'Failed to fetch geocoding data: {str(e)}'
        }, status=500)
    except json.JSONDecodeError as e:
        return JsonResponse({
            'error': f'Invalid response from geocoding service: {str(e)}'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'error': f'Unexpected error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_GET
def forward_geocode(request):
    """
    Proxy endpoint for forward geocoding using Nominatim API.
    This avoids CORS issues when calling the API from the frontend.
    """
    try:
        # Get parameters from the request
        query = request.GET.get('q')
        limit = request.GET.get('limit', '5')
        countrycodes = request.GET.get('countrycodes', 'ph')
        
        if not query:
            return JsonResponse({
                'error': 'Query parameter is required'
            }, status=400)
        
        # Build the Nominatim API URL
        nominatim_url = 'https://nominatim.openstreetmap.org/search'
        params = {
            'format': 'json',
            'q': query,
            'limit': limit,
            'countrycodes': countrycodes,
            'addressdetails': '1',
        }
        
        # Add User-Agent header as required by Nominatim
        headers = {
            'User-Agent': 'PowerMason/1.0 (Project Management System)'
        }
        
        # Make the request to Nominatim
        response = requests.get(nominatim_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the response
        data = response.json()
        
        # Return the data with proper CORS headers
        json_response = JsonResponse(data, safe=False)
        json_response['Access-Control-Allow-Origin'] = '*'
        json_response['Access-Control-Allow-Methods'] = 'GET'
        json_response['Access-Control-Allow-Headers'] = 'Content-Type'
        
        return json_response
        
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'error': f'Failed to fetch geocoding data: {str(e)}'
        }, status=500)
    except json.JSONDecodeError as e:
        return JsonResponse({
            'error': f'Invalid response from geocoding service: {str(e)}'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'error': f'Unexpected error: {str(e)}'
        }, status=500)