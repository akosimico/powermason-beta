# Standard library
import os
import json
import tempfile
import logging
from decimal import Decimal

# Third-party libraries

from django.core.serializers.json import DjangoJSONEncoder

# Setup logger
logger = logging.getLogger(__name__)

# Django imports
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from notifications.models import Notification, NotificationStatus
from authentication.utils.tokens import get_user_profile, verify_user_profile

# Authentication utils & decorators
from authentication.models import UserProfile
from authentication.utils.decorators import verified_email_required, role_required
from authentication.templatetags.role_tags import has_role
from notifications.utils import send_notification

# Local app imports
from .models import (
    ProjectTask, ProgressFile, ProgressUpdate, ProjectScope,
    TaskMaterial, TaskEquipment, TaskManpower, ScopeBudget
)

from .forms import (
    ProjectTaskForm, ProgressUpdateForm,
    TaskMaterialFormSet, TaskEquipmentFormSet, TaskManpowerFormSet
)
from .utils.pdf_reader import extract_project_info
from project_profiling.models import ProjectProfile
from project_profiling.utils import recalc_project_progress
@login_required
def progress_history(request):
    """
    Global progress history with filters.
    """
    updates = ProgressUpdate.objects.select_related(
        "task__project", "reported_by", "reviewed_by"
    ).prefetch_related("attachments").order_by("-created_at")

    # --- Filters ---
    project_id = request.GET.get("project")
    status = request.GET.get("status")
    reporter_id = request.GET.get("reporter")

    if project_id and project_id.isdigit():
        updates = updates.filter(task__project_id=project_id)

    if status in ["P", "A", "R"]:
        updates = updates.filter(status=status)

    if reporter_id and reporter_id.isdigit():
        updates = updates.filter(reported_by_id=reporter_id)

    projects = ProjectProfile.objects.all()
    reporters = UserProfile.objects.all()

    return render(request, "progress/progress_history.html", {
        "updates": updates,
        "projects": projects,
        "reporters": reporters,
        "selected_project": project_id,
        "selected_status": status,
        "selected_reporter": reporter_id,
    })


@login_required
def submit_progress_update(request, task_id):
    # Get user profile from session
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    task = get_object_or_404(ProjectTask, id=task_id)

    if request.method == "POST":
        form = ProgressUpdateForm(request.POST)
        files = request.FILES.getlist("attachments")

        if form.is_valid():
            # Save progress update
            update = form.save(commit=False)
            update.task = task
            update.reported_by = verified_profile
            update.save()

            # Save attachments
            for f in files:
                ProgressFile.objects.create(update=update, file=f)

            # Notify OMs and EGs
            om_eg_users = UserProfile.objects.filter(role__in=["OM", "EG"])
            notif_message = (
                f"{verified_profile.full_name} submitted a progress report "
                f"for Project '{task.project.project_name}' (Task: {task.task_name})"
            )

            if om_eg_users.exists():
                notif = Notification.objects.create(
                    message=notif_message,
                    link=reverse("review_updates")
                )
                for user in om_eg_users:
                    NotificationStatus.objects.create(notification=notif, user=user)

            # Notify the PM themselves
            notif_pm = Notification.objects.create(
                message=f"You submitted a progress report for Project '{task.project.project_name}' (Task: {task.task_name})",
                link=reverse("task_list", kwargs={
                    "project_id": task.project.id
                })
            )
            NotificationStatus.objects.create(notification=notif_pm, user=verified_profile)

            # Success message for PM
            messages.success(
                request,
                "Your report has been submitted. Operations Managers / Engineers have been notified, and you also have a record in your notifications."
            )

            # Redirect back to task list
            return redirect(reverse("task_list", kwargs={
                "project_id": task.project.id
            }))
        else:
            messages.error(request, "Failed to submit report. Please check the form.")

    else:
        form = ProgressUpdateForm()

    return render(request, "progress/submit_update.html", {
        "form": form,
        "task": task,
        "role": verified_profile.role,
    })


@login_required
def get_pending_count(request):
    if has_role(request.user, "OM") or has_role(request.user, "EG") or request.user.is_superuser:
        pending_count = ProgressUpdate.objects.filter(status="P").count()
    else:
        pending_count = 0
    return JsonResponse({"pending_count": pending_count})


@login_required
@verified_email_required
@role_required("EG", "OM")
def review_updates(request):
    """
    Global view for OM/EG and superusers to see all pending updates.
    """
    pending_updates = ProgressUpdate.objects.filter(status="P")
    context = {
        "updates": pending_updates,
    }
    return render(request, "progress/review_updates.html", context)

@login_required
@verified_email_required
@role_required("EG", "OM")
def approve_update(request, update_id):
    update = get_object_or_404(ProgressUpdate, id=update_id)

    update.status = "A"
    update.reviewed_by = request.user.userprofile
    update.reviewed_at = timezone.now()
    update.save(update_fields=["status", "reviewed_by", "reviewed_at"])

    task = update.task
    approved_updates = task.updates.filter(status="A")
    total_progress = sum(u.progress_percent for u in approved_updates)
    task.progress = min(total_progress, 100)

    if task.progress >= 100:
        task.is_completed = True
        task.status = "CP"
    elif task.progress > 0:
        task.is_completed = False
        task.status = "OG"
    else:
        task.is_completed = False
        task.status = "PL"

    task.save(update_fields=["progress", "is_completed", "status"])

    task.project.update_progress_from_tasks()

    messages.success(request, f"Progress update for '{task.task_name}' approved successfully.")
    return redirect("review_updates")

@login_required
@verified_email_required
@role_required("EG", "OM")
def reject_update(request, update_id):
    update = get_object_or_404(ProgressUpdate, id=update_id)
    update.status = "R"
    update.reviewed_by = request.user.userprofile
    update.reviewed_at = timezone.now()
    update.save()
    messages.warning(request, f"Progress update for '{update.task.task_name}' has been rejected.")

    return redirect("review_updates")


@login_required
@verified_email_required
@role_required("PM", "OM", "EG")
def task_list(request, project_id):
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    project = get_object_or_404(ProjectProfile, id=project_id)
    
    show_archived = request.GET.get("show") == "archived"
    
    if verified_profile.role == "PM":
        tasks = project.tasks.filter(assigned_to=request.user.userprofile)
    else:
        tasks = project.tasks.all()
    
    # ✅ Only archived OR only active
    if show_archived:
        tasks = tasks.filter(is_archived=True)
    else:
        tasks = tasks.filter(is_archived=False)

    # Prefetch the latest approved progress for each task
    for task in tasks:
        latest_update = task.updates.filter(status='A').order_by('-created_at').first()
        task.latest_progress = latest_update.progress_percent if latest_update else 0
        task.is_completed = task.latest_progress >= 100  # mark as completed if 100%

    return_url = request.GET.get('return_url') or f"scheduling/{project_id}/tasks/"

     
    return render(request, "scheduling/task_list.html", {
        "project": project,
        "tasks": tasks,
        "role": verified_profile.role,
        "show_archived": show_archived,
        "return_url": return_url,
    })



# def parse_excel(file):
#     df = pd.read_excel(file)
#     tasks = []
#     for _, row in df.iterrows():
#         tasks.append({
#             "task_name": row.get("Task"),
#             "start_date": row.get("Start"),
#             "end_date": row.get("End"),
#             "duration_days": row.get("Days"),
#             "manhours": row.get("MH"),
#             "scope": row.get("Scope"),
#         })
#     return tasks

@require_http_methods(["POST"])
def create_scope_ajax(request, project_id):
    try:
        project = get_object_or_404(ProjectProfile, id=project_id)
        
        # Parse JSON data
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        weight = float(data.get('weight', 0))
        
        # Validation
        if not name:
            return JsonResponse({'error': 'Scope name is required'}, status=400)
        
        if weight <= 0 or weight > 100:
            return JsonResponse({'error': 'Weight must be between 0 and 100'}, status=400)
        
        # Check if total weight would exceed 100%
        existing_total = sum(float(scope.weight) for scope in project.scopes.all())
        if existing_total + weight > 100:
            remaining = 100 - existing_total
            return JsonResponse({
                'error': f'Total weight would exceed 100%. Maximum available: {remaining:.2f}%'
            }, status=400)
        
        # Create the scope
        scope = ProjectScope.objects.create(
            project=project,
            name=name,
            weight=weight
        )
        
        return JsonResponse({
            'id': scope.id,
            'name': scope.name,
            'weight': str(scope.weight)
        })
        
    except ValueError:
        return JsonResponse({'error': 'Invalid weight value'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@login_required
@verified_email_required
@role_required("EG", "OM")
def task_create(request, project_id):
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    project = get_object_or_404(ProjectProfile, id=project_id)

    # Filter scopes to only show those that have budget planning data
    budget_scopes = ProjectScope.objects.filter(
        project=project,
        is_deleted=False,
        budget_categories__isnull=False
    ).distinct().order_by('name')

    # Calculate remaining weights
    scope_remaining = {}
    for scope in budget_scopes:
        total_weight = sum(t.weight for t in scope.tasks.all())
        scope_remaining[scope.id] = max(0, scope.weight - total_weight)

    if request.method == "POST":
        form = ProjectTaskForm(request.POST, project=project)
        # Initialize formsets with project context
        material_formset = TaskMaterialFormSet(request.POST, prefix='materials')
        equipment_formset = TaskEquipmentFormSet(request.POST, prefix='equipment')
        manpower_formset = TaskManpowerFormSet(request.POST, prefix='manpower')

        # Pass project to each form in formsets
        for mat_form in material_formset:
            mat_form.project = project
        for eq_form in equipment_formset:
            eq_form.project = project

        if form.is_valid() and material_formset.is_valid() and equipment_formset.is_valid() and manpower_formset.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.save()
            form.save_m2m()

            # Save resources
            material_formset.instance = task
            material_formset.save()

            equipment_formset.instance = task
            equipment_formset.save()

            manpower_formset.instance = task
            manpower_formset.save()

            messages.success(request, f"Task '{task.task_name}' and resources created successfully!")
            return redirect("task_list", project.id)
        else:
            messages.error(request, "Please check the form and correct any errors.")
    else:
        form = ProjectTaskForm(project=project)
        material_formset = TaskMaterialFormSet(prefix='materials', queryset=TaskMaterial.objects.none())
        equipment_formset = TaskEquipmentFormSet(prefix='equipment', queryset=TaskEquipment.objects.none())
        manpower_formset = TaskManpowerFormSet(prefix='manpower', queryset=TaskManpower.objects.none())

        # Pass project to forms
        for mat_form in material_formset:
            mat_form.project = project
        for eq_form in equipment_formset:
            eq_form.project = project

    return render(request, "scheduling/task_form.html", {
        "form": form,
        "material_formset": material_formset,
        "equipment_formset": equipment_formset,
        "manpower_formset": manpower_formset,
        "project": project,
        "budget_scopes": budget_scopes,
        "role": verified_profile.role,
        "scope_remaining_json": json.dumps(scope_remaining, cls=DjangoJSONEncoder),
    })

# @login_required
# @verified_email_required
# @role_required("EG", "OM")
# def save_imported_tasks(request, project_id, token, role):
#     verified_profile = verify_user_token(request, token, role)
#     if isinstance(verified_profile, HttpResponse):
#         return verified_profile

#     project = get_object_or_404(ProjectProfile, id=project_id)

#     if request.method == "POST":
#         task_count = int(request.POST.get("task_count", 0))

#         global_scope = request.POST.get("global_scope") or None
#         assigned_to_id = request.POST.get("global_assigned_to") or None
#         assigned_user_global = (
#             UserProfile.objects.filter(id=assigned_to_id).first()
#             if assigned_to_id else None
#         )

#         task_objs = []
#         for i in range(task_count):
#             task_name = request.POST.get(f"task_name_{i}")
#             if not task_name: 
#                 continue

#             start_date = parse_date(request.POST.get(f"start_date_{i}"))
#             end_date = parse_date(request.POST.get(f"end_date_{i}"))
#             duration = request.POST.get(f"duration_days_{i}")
#             manhours = request.POST.get(f"manhours_{i}")

#             # Weight
#             weight_str = request.POST.get(f"weight_{i}", "").strip()
#             weight = float(weight_str) if weight_str else 0.0

#             # Scope (per-task overrides global)
#             scope_i = request.POST.get(f"scope_{i}") or None
#             scope = scope_i if scope_i else global_scope

#             # Assigned to (per-task overrides global)
#             assigned_to_id_i = request.POST.get(f"assigned_to_{i}") or None
#             assigned_user = (
#                 UserProfile.objects.filter(id=assigned_to_id_i).first()
#                 if assigned_to_id_i else assigned_user_global
#             )

#             task_objs.append(ProjectTask(
#                 project=project,
#                 task_name=task_name,
#                 start_date=start_date,
#                 end_date=end_date,
#                 duration_days=duration,
#                 manhours=manhours,
#                 weight=weight,
#                 scope=scope,
#                 assigned_to=assigned_user,
#             ))

#         if task_objs:
#             ProjectTask.objects.bulk_create(task_objs)
#         else:
#             print("No tasks to save.")  # DEBUG

#         return redirect("task_list", project.id)

    # return redirect("task_create", project.id, token, role)


@login_required
@verified_email_required
@role_required("EG", "OM")
def task_update(request, project_id, task_id):
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    project = get_object_or_404(ProjectProfile, id=project_id)
    task = get_object_or_404(ProjectTask, id=task_id, project=project)
    
    # Filter scopes to only show those that have budget planning data
    # This ensures only scopes created during budget planning are available
    budget_scopes = ProjectScope.objects.filter(
        project=project,
        is_deleted=False,
        budget_categories__isnull=False  # Only scopes with budget entries
    ).distinct().order_by('name')
    
    # Calculate remaining weights for budget planning scopes only
    scope_remaining = {}
    for scope in budget_scopes:
        # Exclude current task's weight when calculating remaining
        total_weight = sum(t.weight for t in scope.tasks.exclude(id=task.id))
        scope_remaining[scope.id] = max(0, scope.weight - total_weight)

    if request.method == "POST":
        form = ProjectTaskForm(request.POST, instance=task, project=project)
        assigned_to_id = request.POST.get("assigned_to")

        if form.is_valid():
            try:
                task = form.save(commit=False)
                if assigned_to_id:
                    assigned_user = UserProfile.objects.filter(id=assigned_to_id).first()
                    task.assigned_to = assigned_user
                task.save()
                form.save_m2m()
                messages.success(request, f"Task '{task.task_name}' updated successfully!")
                return redirect("task_list", project.id)
            except Exception as e:
                messages.error(request, f"Error updating task: {str(e)}")
        else:
            messages.error(request, "Invalid form data. Please correct the errors below.")
    else:
        form = ProjectTaskForm(instance=task, project=project)

    context = {
        "form": form,
        "project": project,
        "task": task,
        "role": verified_profile.role,
        "budget_scopes": budget_scopes,  # Pass filtered scopes
        "project_managers": UserProfile.objects.filter(role="PM"),
        "scope_remaining_json": json.dumps(scope_remaining, cls=DjangoJSONEncoder),
    }
    return render(request, "scheduling/task_edit.html", context)


@login_required
@verified_email_required
@role_required("EG", "OM")
def task_bulk_archive(request, project_id):
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    project = get_object_or_404(ProjectProfile, id=project_id)

    if request.method == "POST":
        task_ids = request.POST.getlist("task_ids")
        if task_ids:
            updated_count = ProjectTask.objects.filter(
                id__in=task_ids, project=project
            ).update(is_archived=True)
            messages.success(request, f"Archived {updated_count} task(s).")
        else:
            messages.warning(request, "No tasks were selected.")

    return redirect("task_list", project.id)

def task_bulk_unarchive(request, project_id):
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")
        
    if request.method == "POST":
        task_ids = request.POST.getlist("task_ids")
        ProjectTask.objects.filter(id__in=task_ids).update(is_archived=False)
        messages.success(request, "Selected tasks unarchived successfully.")
    return redirect("task_list", project_id=project_id)


@login_required
@verified_email_required
@role_required("EG", "OM")
def task_archive(request, project_id, task_id):
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    project = get_object_or_404(ProjectProfile, id=project_id)
    task = get_object_or_404(ProjectTask, id=task_id, project=project)

    if request.method == "POST":
        try:
            task_name = task.task_name
            task.is_archived = True
            task.save()
            messages.success(request, f"Task '{task_name}' has been archived successfully.")
        except Exception as e:
            messages.error(request, f"Error archiving task: {str(e)}")
        return redirect("task_list", project.id)

    return render(request, "scheduling/task_confirm_archive.html", {
        "task": task,
        "project": project,
        "role": verified_profile.role,
    })

@login_required
@verified_email_required
@role_required("OM", "EG")
def task_unarchive(request, project_id, task_id):
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    project = get_object_or_404(ProjectProfile, id=project_id)
    task = get_object_or_404(ProjectTask, id=task_id, project=project)

    task.is_archived = False
    task.save()

    messages.success(request, f"Task '{task.name}' has been unarchived.")
    return redirect("task_list", project_id=project.id)


@login_required
@verified_email_required
@role_required('EG', 'OM')
def scope_budget_allocation(request, project_id):
    """
    Allocate project budget across scopes
    """
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")
        
    project = get_object_or_404(ProjectProfile, id=project_id)
    
    # Check if budget is approved
    if not project.approved_budget:
        messages.warning(request, "Budget must be approved before scope allocation can begin.")
        return redirect('project_view', project_source=project.project_source, pk=project_id)
    
    # Get all scopes for this project
    scopes = project.scopes.filter(is_deleted=False)
    
    # Get existing scope budgets
    scope_budgets = ScopeBudget.objects.filter(project=project)
    budget_dict = {sb.scope: sb for sb in scope_budgets}
    
    # Calculate totals
    total_allocated = sum(sb.allocated_amount for sb in scope_budgets)
    remaining_budget = project.approved_budget - total_allocated
    
    if request.method == 'POST':
        # Process form submission
        total_requested = 0
        allocations = []
        
        for scope in scopes:
            amount_key = f'amount_{scope.id}'
            amount = request.POST.get(amount_key, '0')
            
            try:
                amount = Decimal(amount) if amount else Decimal('0')
                if amount > 0:
                    allocations.append((scope, amount))
                    total_requested += amount
            except (ValueError, TypeError):
                messages.error(request, f"Invalid amount for scope '{scope.name}'")
                return redirect('scope_budget_allocation', project_id=project_id)
        
        # Validate total doesn't exceed approved budget
        if total_requested > project.approved_budget:
            messages.error(request, f"Total allocation (₱{total_requested:,.2f}) exceeds approved budget (₱{project.approved_budget:,.2f})")
            return redirect('scope_budget_allocation', project_id=project_id)
        
        # Save allocations
        try:
            for scope, amount in allocations:
                scope_budget, created = ScopeBudget.objects.get_or_create(
                    project=project,
                    scope=scope,
                    defaults={'allocated_amount': amount}
                )
                if not created:
                    scope_budget.allocated_amount = amount
                    scope_budget.save()
            
            # Remove allocations for scopes not in the form
            existing_scopes = {scope for scope, _ in allocations}
            ScopeBudget.objects.filter(project=project).exclude(scope__in=existing_scopes).delete()
            
            messages.success(request, f"Budget allocation updated successfully. Total allocated: ₱{total_requested:,.2f}")
            return redirect('scope_budget_allocation', project_id=project_id)
            
        except Exception as e:
            messages.error(request, f"Error saving budget allocation: {str(e)}")
            return redirect('scope_budget_allocation', project_id=project_id)
    
    # Prepare scope data for template
    scope_data = []
    for scope in scopes:
        budget = budget_dict.get(scope)
        scope_data.append({
            'scope': scope,
            'budget': budget,
            'allocated_amount': budget.allocated_amount if budget else 0,
            'allocated_to_tasks': budget.allocated_to_tasks if budget else 0,
            'remaining_budget': budget.remaining_budget if budget else 0,
            'utilization_percentage': budget.utilization_percentage if budget else 0,
        })
    
    return render(request, 'scheduling/scope_budget_allocation.html', {
        'project': project,
        'scopes': scope_data,
        'total_allocated': total_allocated,
        'remaining_budget': remaining_budget,
        'budget_utilization': (total_allocated / project.approved_budget * 100) if project.approved_budget > 0 else 0,
        'role': verified_profile.role,
    })


# ========================================
# SCHEDULE MANAGEMENT VIEWS
# Excel template generation and upload workflow
# ========================================

@login_required
@verified_email_required
@role_required("PM", "OM", "EG")
def generate_schedule_template(request, project_id):
    """Generate Excel template for project schedule"""
    from authentication.utils.toast_helpers import set_toast_message
    from .models import ScheduleTemplate, ProjectSchedule
    from .schedule_generator import generate_schedule_template as generate_template

    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    project = get_object_or_404(ProjectProfile, id=project_id)

    # Check if schedule already approved
    approved_schedule = ProjectSchedule.objects.filter(
        project=project,
        status='APPROVED'
    ).first()

    if approved_schedule:
        set_toast_message(request, "This project already has an approved schedule.", "error")
        return redirect('project_view', project_source=project.project_source, pk=project.id)

    # Check if project has scopes
    if not project.scopes.filter(is_deleted=False).exists():
        set_toast_message(request, "Cannot generate template: Project has no scopes defined.", "error")
        return redirect('project_view', project_source=project.project_source, pk=project.id)

    try:
        # Generate template
        relative_path = generate_template(project)

        # Save template record
        template = ScheduleTemplate.objects.create(
            project=project,
            template_file=relative_path,
            generated_by=verified_profile
        )

        set_toast_message(request, "Schedule template generated successfully!", "success")

        # Return file download
        from django.http import FileResponse
        import os
        from django.conf import settings

        file_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'

        # Mark as downloaded
        template.is_downloaded = True
        template.save()

        return response

    except Exception as e:
        logger.error(f"Error generating schedule template: {str(e)}")
        set_toast_message(request, f"Error generating template: {str(e)}", "error")
        return redirect('project_view', project_source=project.project_source, pk=project.id)


@login_required
@verified_email_required
@role_required("PM")
def upload_project_schedule(request, project_id):
    """Upload and parse project schedule Excel file"""
    from authentication.utils.toast_helpers import set_toast_message
    from .models import ProjectSchedule
    from .forms import ProjectScheduleForm
    from .schedule_reader import parse_schedule_excel

    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    project = get_object_or_404(ProjectProfile, id=project_id)

    # Check if approved schedule exists
    approved_schedule = ProjectSchedule.objects.filter(
        project=project,
        status='APPROVED'
    ).first()

    if approved_schedule:
        set_toast_message(request, "Cannot upload: Project already has an approved schedule.", "error")
        return redirect('project_view', project_source=project.project_source, pk=project.id)

    # Check upload limit
    existing_count = ProjectSchedule.objects.filter(project=project).count()
    if existing_count >= 5:
        set_toast_message(request, "Maximum upload limit reached (5 attempts).", "error")
        return redirect('project_view', project_source=project.project_source, pk=project.id)

    if request.method == 'POST':
        form = ProjectScheduleForm(request.POST, request.FILES, project=project)

        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.project = project
            schedule.uploaded_by = verified_profile
            schedule.version = existing_count + 1
            schedule.status = 'DRAFT'
            schedule.save()

            # Parse the uploaded file
            file_path = schedule.file.path

            try:
                parse_result = parse_schedule_excel(file_path, project)

                # Store parsed data and validation results
                schedule.parsed_data = {
                    'scopes': parse_result.get('scopes', []),
                    'task_count': parse_result.get('task_count', 0)
                }
                schedule.task_count = parse_result.get('task_count', 0)
                schedule.validation_errors = {
                    'errors': parse_result.get('errors', []),
                    'warnings': parse_result.get('warnings', [])
                }
                schedule.save()

                if parse_result.get('success'):
                    set_toast_message(
                        request,
                        f"Schedule uploaded successfully! Found {schedule.task_count} tasks.",
                        "success"
                    )
                    return redirect('schedule_detail', schedule_id=schedule.id)
                else:
                    set_toast_message(
                        request,
                        f"Schedule uploaded but has validation errors. Please review.",
                        "warning"
                    )
                    return redirect('schedule_detail', schedule_id=schedule.id)

            except Exception as e:
                logger.error(f"Error parsing schedule: {str(e)}")
                schedule.validation_errors = {
                    'errors': [f"Error parsing file: {str(e)}"],
                    'warnings': []
                }
                schedule.save()
                set_toast_message(request, f"Error parsing schedule: {str(e)}", "error")
                return redirect('schedule_detail', schedule_id=schedule.id)
        else:
            set_toast_message(request, "Please fix the form errors.", "error")
    else:
        form = ProjectScheduleForm(project=project)

    attempts_remaining = 5 - existing_count

    return render(request, 'scheduling/schedule_upload.html', {
        'form': form,
        'project': project,
        'role': verified_profile.role,
        'existing_count': existing_count,
        'attempts_remaining': attempts_remaining,
    })


@login_required
@verified_email_required
def schedule_detail(request, schedule_id):
    """View schedule details and parsed data"""
    from authentication.utils.toast_helpers import set_toast_message
    from .models import ProjectSchedule
    from .task_creator import get_schedule_summary

    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    schedule = get_object_or_404(ProjectSchedule, id=schedule_id)
    project = schedule.project

    # Get summary statistics
    summary = get_schedule_summary(schedule)

    # Get validation errors
    validation_errors = schedule.validation_errors.get('errors', [])
    validation_warnings = schedule.validation_errors.get('warnings', [])

    return render(request, 'scheduling/schedule_detail.html', {
        'schedule': schedule,
        'project': project,
        'role': verified_profile.role,
        'summary': summary,
        'errors': validation_errors,
        'warnings': validation_warnings,
        'can_submit': schedule.can_submit and verified_profile.role == 'PM',
        'can_approve': schedule.can_approve and verified_profile.role in ['OM', 'EG'],
    })


@login_required
@verified_email_required
@role_required("PM")
def submit_schedule_for_approval(request, schedule_id):
    """Submit schedule for OM/EG approval"""
    from authentication.utils.toast_helpers import set_toast_message
    from .models import ProjectSchedule
    from notifications.utils import send_notification

    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    schedule = get_object_or_404(ProjectSchedule, id=schedule_id)

    # Verify PM owns this schedule
    if schedule.uploaded_by != verified_profile:
        set_toast_message(request, "You can only submit schedules you uploaded.", "error")
        return redirect('schedule_detail', schedule_id=schedule.id)

    # Check if can submit with detailed logging
    if not schedule.can_submit:
        # Debug logging to understand why submission failed
        logger.error(f"=== SCHEDULE SUBMISSION BLOCKED ===")
        logger.error(f"Schedule ID: {schedule.id}")
        logger.error(f"Project: {schedule.project.project_id}")
        logger.error(f"Status: {schedule.status}")
        logger.error(f"Validation Errors Field: {schedule.validation_errors}")
        logger.error(f"Validation Errors Type: {type(schedule.validation_errors)}")

        # Check what's in validation_errors
        if schedule.validation_errors:
            errors_list = schedule.validation_errors.get('errors', [])
            warnings_list = schedule.validation_errors.get('warnings', [])
            logger.error(f"Errors List: {errors_list}")
            logger.error(f"Errors Count: {len(errors_list)}")
            logger.error(f"Warnings List: {warnings_list}")
            logger.error(f"Warnings Count: {len(warnings_list)}")

        logger.error(f"can_submit result: {schedule.can_submit}")
        logger.error(f"=== END DEBUG ===")

        # Provide detailed error message based on the reason
        if schedule.status != 'DRAFT':
            error_msg = f"Cannot submit: Schedule is already {schedule.get_status_display()}. Only DRAFT schedules can be submitted."
        elif schedule.validation_errors:
            errors_list = schedule.validation_errors.get('errors', [])
            if errors_list:
                error_msg = f"Cannot submit: {len(errors_list)} validation error(s) found. Please fix and re-upload."
            else:
                error_msg = "Cannot submit: Unknown validation issue. Check logs for details."
        else:
            error_msg = "Cannot submit: Unknown error. Check logs for details."

        set_toast_message(request, error_msg, "error")
        return redirect('schedule_detail', schedule_id=schedule.id)

    if request.method == 'POST':
        # Change status to PENDING
        schedule.status = 'PENDING'
        schedule.submitted_at = timezone.now()
        schedule.save()

        # Notify OM and EG users
        om_eg_users = UserProfile.objects.filter(role__in=['OM', 'EG'])
        notif_message = f'Schedule Pending Approval: Project {schedule.project.project_id} v{schedule.version} submitted by {verified_profile.full_name}'

        if om_eg_users.exists():
            notif = Notification.objects.create(
                message=notif_message,
                link=reverse('review_project_schedule', args=[schedule.id])
            )
            for user in om_eg_users:
                NotificationStatus.objects.create(notification=notif, user=user)

        set_toast_message(request, "Schedule submitted for approval!", "success")
        return redirect('schedule_detail', schedule_id=schedule.id)

    return redirect('schedule_detail', schedule_id=schedule.id)


@login_required
@verified_email_required
@role_required("OM", "EG")
def review_schedules(request):
    """List all pending schedules for review"""
    from .models import ProjectSchedule

    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    pending_schedules = ProjectSchedule.objects.filter(
        status='PENDING'
    ).select_related('project', 'uploaded_by').order_by('-submitted_at')

    return render(request, 'scheduling/review_schedules.html', {
        'schedules': pending_schedules,
        'role': verified_profile.role,
    })


@login_required
@verified_email_required
@role_required("OM", "EG")
def review_project_schedule(request, schedule_id):
    """Review a specific schedule for approval/rejection"""
    from .models import ProjectSchedule
    from .task_creator import get_schedule_summary

    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    schedule = get_object_or_404(ProjectSchedule, id=schedule_id)
    project = schedule.project

    # Get summary statistics
    summary = get_schedule_summary(schedule)

    # Get parsed scope data
    scopes_data = schedule.parsed_data.get('scopes', [])

    return render(request, 'scheduling/schedule_review.html', {
        'schedule': schedule,
        'project': project,
        'role': verified_profile.role,
        'summary': summary,
        'scopes_data': scopes_data,
    })


@login_required
@verified_email_required
@role_required("OM", "EG")
def approve_schedule(request, schedule_id):
    """Approve schedule and create tasks"""
    from authentication.utils.toast_helpers import set_toast_message
    from .models import ProjectSchedule
    from .task_creator import create_tasks_from_schedule
    from notifications.utils import send_notification

    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    schedule = get_object_or_404(ProjectSchedule, id=schedule_id)

    if not schedule.can_approve:
        set_toast_message(request, "This schedule cannot be approved.", "error")
        return redirect('review_project_schedule', schedule_id=schedule.id)

    if request.method == 'POST':
        try:
            # Create tasks from schedule
            result = create_tasks_from_schedule(schedule)

            if result['success']:
                # Update schedule status
                schedule.status = 'APPROVED'
                schedule.reviewed_by = verified_profile
                schedule.reviewed_at = timezone.now()
                schedule.is_active = True
                schedule.deactivate_other_schedules()
                schedule.save()

                # Notify PM
                notif = Notification.objects.create(
                    message=f'Schedule Approved: Your schedule for {schedule.project.project_id} has been approved. {result["created_count"]} tasks created.',
                    link=reverse('task_list', args=[schedule.project.id])
                )
                NotificationStatus.objects.create(notification=notif, user=schedule.uploaded_by)

                set_toast_message(
                    request,
                    f"Schedule approved! {result['created_count']} tasks created successfully.",
                    "success"
                )
                return redirect('task_list', project_id=schedule.project.id)
            else:
                set_toast_message(
                    request,
                    f"Error creating tasks: {result.get('error', 'Unknown error')}",
                    "error"
                )
                return redirect('review_project_schedule', schedule_id=schedule.id)

        except Exception as e:
            logger.error(f"Error approving schedule: {str(e)}")
            set_toast_message(request, f"Error approving schedule: {str(e)}", "error")
            return redirect('review_project_schedule', schedule_id=schedule.id)

    return redirect('review_project_schedule', schedule_id=schedule.id)


@login_required
@verified_email_required
@role_required("OM", "EG")
def reject_schedule(request, schedule_id):
    """Reject schedule with reason"""
    from authentication.utils.toast_helpers import set_toast_message
    from .models import ProjectSchedule
    from .forms import ScheduleRejectionForm
    from notifications.utils import send_notification

    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    schedule = get_object_or_404(ProjectSchedule, id=schedule_id)

    if not schedule.can_approve:
        set_toast_message(request, "This schedule cannot be rejected.", "error")
        return redirect('review_project_schedule', schedule_id=schedule.id)

    if request.method == 'POST':
        form = ScheduleRejectionForm(request.POST)

        if form.is_valid():
            rejection_reason = form.cleaned_data['rejection_reason']

            # Update schedule
            schedule.status = 'REJECTED'
            schedule.reviewed_by = verified_profile
            schedule.reviewed_at = timezone.now()
            schedule.rejection_reason = rejection_reason
            schedule.save()

            # Notify PM
            notif = Notification.objects.create(
                message=f'Schedule Rejected: Your schedule for {schedule.project.project_id} has been rejected. Reason: {rejection_reason[:100]}...',
                link=reverse('schedule_detail', args=[schedule.id])
            )
            NotificationStatus.objects.create(notification=notif, user=schedule.uploaded_by)

            set_toast_message(request, "Schedule rejected. PM has been notified.", "success")
            return redirect('review_schedules')
        else:
            set_toast_message(request, "Please provide a rejection reason.", "error")
    else:
        form = ScheduleRejectionForm()

    return render(request, 'scheduling/schedule_reject.html', {
        'form': form,
        'schedule': schedule,
        'project': schedule.project,
        'role': verified_profile.role,
    })
