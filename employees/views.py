# employees/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.utils.decorators import method_decorator
from datetime import date, timedelta
from django.views.decorators.http import require_http_methods, require_POST
import csv
import logging

from .models import Employee, ProjectAssignment
from .forms import EmployeeForm, EmployeeFilterForm
from authentication.models import UserProfile
from authentication.utils.decorators import verified_email_required, role_required
from project_profiling.models import ProjectProfile
from manage_client.models import Client

logger = logging.getLogger(__name__)


@method_decorator([login_required, verified_email_required], name='dispatch')
class EmployeeListView(ListView):
    """List all employees with filtering and search functionality"""
    model = Employee
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Employee.objects.select_related('user_profile__user').prefetch_related('project_assignments')
        
        # Get filter parameters
        search = self.request.GET.get('search', '').strip()
        role_filter = self.request.GET.get('role', '')
        status_filter = self.request.GET.get('status', '')
        contract_status = self.request.GET.get('contract_status', '')
        
        # Apply search filter
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(employee_id__icontains=search) |
                Q(email__icontains=search)
            )
        
        # Apply role filter
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        
        # Apply status filter
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Apply contract status filter
        if contract_status == 'expiring':
            queryset = queryset.expiring_soon()
        elif contract_status == 'expired':
            queryset = queryset.expired()
        
        return queryset.order_by('last_name', 'first_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter form
        context['filter_form'] = EmployeeFilterForm(self.request.GET)
        
        # Add statistics
        context['stats'] = {
            'total_employees': Employee.objects.count(),
            'active_employees': Employee.objects.active().count(),
            'project_managers': Employee.objects.project_managers().count(),
            'expiring_contracts': Employee.objects.expiring_soon().count(),
            'expired_contracts': Employee.objects.expired().count(),
        }
        
        # Preserve search parameters for pagination
        context['search_params'] = self.request.GET.copy()
        if 'page' in context['search_params']:
            del context['search_params']['page']
        
        return context


@method_decorator([login_required, verified_email_required], name='dispatch')
class EmployeeDetailView(DetailView):
    """Detail view for a single employee"""
    model = Employee
    template_name = 'employees/employee_detail.html'
    context_object_name = 'employee'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user role for project filtering
        user_profile = self.request.user.userprofile
        user_role = user_profile.role
        
        # Filter projects based on user role
        if user_role == "PM":
            projects = ProjectProfile.objects.filter(project_manager=user_profile)
        elif user_role == "VO":
            try:
                user_email = user_profile.user.email
                if user_email:
                    matching_clients = Client.objects.filter(email=user_email)
                    if matching_clients.exists():
                        projects = ProjectProfile.objects.filter(client__in=matching_clients)
                    else:
                        projects = ProjectProfile.objects.none()
                else:
                    projects = ProjectProfile.objects.none()
            except Client.DoesNotExist:
                projects = ProjectProfile.objects.none()
        else:
            # For admin users or other roles
            projects = ProjectProfile.objects.all()
        
        # Get projects where this employee's user_profile is the project_manager
        project_assignments = []
        if self.object.user_profile:
            # Get projects where this employee (via their user_profile) is the project_manager
            assigned_projects = ProjectProfile.objects.filter(
                project_manager=self.object.user_profile
            ).filter(id__in=[p.id for p in projects])  # Filter by accessible projects
            
            # Convert to a list format similar to project assignments
            project_assignments = []
            for project in assigned_projects:
                project_assignments.append({
                    'project': project,
                    'assigned_date': project.created_at.date() if project.created_at else None,
                    'end_date': project.target_completion_date,
                    'is_lead': True,  # PM is always lead
                    'is_active': project.status in ['PL', 'OG'],  # Planned or Ongoing
                })
        
        context['project_assignments'] = project_assignments
        
        # Contract information
        context['contract_info'] = {
            'is_expired': self.object.is_contract_expired,
            'days_until_expiry': self.object.days_until_contract_expiry,
            'expiring_soon': self.object.contract_expiring_soon,
        }
        
        # Get available user profiles for assignment (only PM roles)
        # First, get all user profiles that are already assigned to employees (excluding current employee)
        assigned_profile_ids = Employee.objects.filter(
            user_profile__isnull=False
        ).exclude(pk=self.object.pk).values_list('user_profile_id', flat=True)
        
        # Get available user profiles with PM role (excluding already assigned ones)
        available_user_profiles = UserProfile.objects.select_related('user').filter(
            role='PM'
        ).exclude(
            id__in=assigned_profile_ids
        ).order_by('user__email')
        
        context['available_user_profiles'] = available_user_profiles
        
        # Generate token for add user functionality
        from authentication.utils.tokens import make_dashboard_token
        user_profile = self.request.user.userprofile
        context['user_token'] = make_dashboard_token(user_profile)
        
        context['available_user_profiles'] = available_user_profiles
        
        return context


# Update these specific methods in your views.py

@method_decorator([login_required, verified_email_required, role_required('OM', 'EG')], name='dispatch')
class EmployeeCreateView(CreateView):
    """Create a new employee"""
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'
    success_url = reverse_lazy('employee:list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        messages.success(self.request, f'Employee {self.object.full_name} has been created successfully.')
        
        # Log the creation
        logger.info(f'Employee {self.object.full_name} created by {self.request.user}')
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Employee'
        context['submit_text'] = 'Create Employee'
        # Add employee as None for template logic
        context['employee'] = None
        return context


@method_decorator([login_required, verified_email_required, role_required('OM', 'EG')], name='dispatch')
class EmployeeUpdateView(UpdateView):
    """Update an existing employee"""
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'
    
    def get_success_url(self):
        return reverse('employee:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Store original values for comparison
        original_employee = Employee.objects.get(pk=self.object.pk)
        original_role = original_employee.role
        original_status = original_employee.status
        
        # Update the updated_at field manually if your model doesn't auto-update
        form.instance.updated_at = timezone.now()
        
        response = super().form_valid(form)
        
        # Check for important changes
        changes = []
        if original_role != self.object.role:
            changes.append(f'Role changed from {original_employee.get_role_display()} to {self.object.get_role_display()}')
        if original_status != self.object.status:
            changes.append(f'Status changed from {original_employee.get_status_display()} to {self.object.get_status_display()}')
        
        if changes:
            change_msg = '; '.join(changes)
            messages.info(self.request, f'Employee updated. {change_msg}')
            logger.info(f'Employee {self.object.full_name} updated by {self.request.user}: {change_msg}')
        else:
            messages.success(self.request, f'Employee {self.object.full_name} has been updated successfully.')
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit {self.object.full_name}'
        context['submit_text'] = 'Update Employee'
        # Pass the employee object to template
        context['employee'] = self.object
        return context


@method_decorator([login_required, verified_email_required, role_required('OM', 'EG')], name='dispatch')
class EmployeeDeleteView(DeleteView):
    """Soft delete an employee (set status to terminated)"""
    model = Employee
    template_name = 'employees/employee_confirm_delete.html'
    success_url = reverse_lazy('employee:list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Instead of deleting, set status to terminated
        self.object.status = 'terminated'
        self.object.save()
        
        messages.success(request, f'Employee {self.object.full_name} has been terminated.')
        logger.info(f'Employee {self.object.full_name} terminated by {request.user}')
        
        return redirect(self.success_url)


@login_required
@verified_email_required
def employee_dashboard(request):
    """Dashboard showing employee statistics and alerts"""
    
    # Get key statistics
    stats = {
        'total_employees': Employee.objects.count(),
        'active_employees': Employee.objects.active().count(),
        'inactive_employees': Employee.objects.filter(status='inactive').count(),
        'project_managers': Employee.objects.project_managers().count(),
    }
    
    # Contract alerts - only show unnotified contracts (consistent with notifications page)
    expiring_soon = Employee.objects.expiring_soon(days=30).filter(contract_expiry_notified=False)
    expired = Employee.objects.expired().filter(contract_expiry_notified=False)
    
    # Recent employees (last 30 days)
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_employees = Employee.objects.filter(
        created_at__date__gte=thirty_days_ago
    ).order_by('-created_at')[:5]
    
    # Role distribution
    role_distribution = Employee.objects.values('role').annotate(
        count=Count('role')
    ).order_by('-count')
    
    context = {
        'stats': stats,
        'expiring_soon': expiring_soon,
        'expired': expired,
        'recent_employees': recent_employees,
        'role_distribution': role_distribution,
    }
    
    return render(request, 'employees/dashboard.html', context)


@login_required
@verified_email_required
@role_required('OM', 'EG')
@require_POST
def manage_user_profile(request, pk):
    """Manage user profile assignment for an employee"""
    employee = get_object_or_404(Employee, pk=pk)
    user_profile_id = request.POST.get('user_profile_id')
    
    try:
        if user_profile_id:
            # Assign new user profile
            user_profile = get_object_or_404(UserProfile, id=user_profile_id)
            
            # Check if this user profile is already assigned to another employee
            existing_assignment = Employee.objects.filter(user_profile=user_profile).exclude(pk=employee.pk).first()
            if existing_assignment:
                messages.error(request, f'User profile {user_profile.user.email} is already assigned to {existing_assignment.full_name}')
                return redirect('employee:detail', pk=employee.pk)
            
            # Remove old assignment if exists
            if employee.user_profile:
                old_profile = employee.user_profile
                employee.user_profile = None
                employee.save()
                logger.info(f'Removed user profile {old_profile.user.email} from {employee.full_name} by {request.user}')
            
            # Assign new profile
            employee.user_profile = user_profile
            employee.save()
            
            messages.success(request, f'User profile {user_profile.user.email} assigned to {employee.full_name}')
            logger.info(f'Assigned user profile {user_profile.user.email} to {employee.full_name} by {request.user}')
        else:
            # Remove user profile assignment
            if employee.user_profile:
                old_profile = employee.user_profile
                employee.user_profile = None
                employee.save()
                messages.success(request, f'User profile {old_profile.user.email} removed from {employee.full_name}')
                logger.info(f'Removed user profile {old_profile.user.email} from {employee.full_name} by {request.user}')
            else:
                messages.info(request, 'No user profile was assigned to this employee')
    
    except Exception as e:
        logger.error(f'Error managing user profile for {employee.full_name}: {e}')
        messages.error(request, 'An error occurred while managing the user profile')
    
    return redirect('employee:detail', pk=employee.pk)


@login_required
@verified_email_required
@role_required('OM', 'EG')
@require_POST
def extend_contract(request, pk):
    """Extend an employee's contract"""
    employee = get_object_or_404(Employee, pk=pk)
    
    try:
        new_end_date = request.POST.get('new_end_date')
        if not new_end_date:
            # If no specific date provided, extend by 1 year
            if employee.contract_end_date:
                from dateutil.relativedelta import relativedelta
                employee.contract_end_date = employee.contract_end_date + relativedelta(years=1)
            else:
                # If no existing contract end date, set to 1 year from today
                employee.contract_end_date = date.today() + relativedelta(years=1)
        else:
            from datetime import datetime
            new_date = datetime.strptime(new_end_date, '%Y-%m-%d').date()
            employee.contract_end_date = new_date
        
        employee.save()
        
        messages.success(request, f'Contract extended for {employee.full_name} until {employee.contract_end_date}')
        logger.info(f'Contract extended for {employee.full_name} by {request.user} until {employee.contract_end_date}')
        
        # If it's an AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Contract extended until {employee.contract_end_date}',
                'new_end_date': str(employee.contract_end_date)
            })
        
    except ValueError:
        error_msg = 'Invalid date format'
        messages.error(request, error_msg)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': error_msg}, status=400)
    except Exception as e:
        logger.error(f'Error extending contract for {employee.full_name}: {e}')
        error_msg = 'Failed to extend contract'
        messages.error(request, error_msg)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': error_msg}, status=500)
    
    return redirect('employee:detail', pk=employee.pk)


@login_required
@verified_email_required
@role_required('OM', 'EG')
@require_POST
def toggle_employee_status(request, pk):
    """Toggle employee status between active and inactive"""
    employee = get_object_or_404(Employee, pk=pk)
    
    try:
        if employee.status == 'active':
            employee.status = 'inactive'
            action = 'deactivated'
        else:
            employee.status = 'active'
            action = 'activated'
        
        employee.save()
        
        messages.success(request, f'Employee {employee.full_name} has been {action}')
        logger.info(f'Employee {employee.full_name} {action} by {request.user}')
        
        # If it's an AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Employee {action}',
                'new_status': employee.status
            })
    
    except Exception as e:
        logger.error(f'Error toggling status for {employee.full_name}: {e}')
        error_msg = 'Failed to update employee status'
        messages.error(request, error_msg)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': error_msg}, status=500)
    
    return redirect('employee:detail', pk=employee.pk)


@login_required
@verified_email_required
@role_required('OM', 'EG')
@require_POST
def assign_to_project(request, pk):
    """Assign employee to a project"""
    employee = get_object_or_404(Employee, pk=pk)
    project_id = request.POST.get('project_id')
    is_lead = request.POST.get('is_lead', False) == 'true'
    
    try:
        if not project_id:
            raise ValueError('Project ID is required')
        
        project = get_object_or_404(ProjectProfile, id=project_id)
        
        # Check if employee is already assigned to this project
        existing_assignment = ProjectAssignment.objects.filter(
            employee=employee,
            project=project,
            is_active=True
        ).first()
        
        if existing_assignment:
            messages.warning(request, f'{employee.full_name} is already assigned to {project.name}')
        else:
            # Create new assignment
            assignment = ProjectAssignment.objects.create(
                employee=employee,
                project=project,
                is_lead=is_lead,
                assigned_date=date.today(),
                assigned_by=request.user
            )
            
            role_text = 'Lead' if is_lead else 'Member'
            messages.success(request, f'{employee.full_name} assigned to {project.name} as {role_text}')
            logger.info(f'{employee.full_name} assigned to {project.name} as {role_text} by {request.user}')
        
        # If it's an AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Employee assigned to project successfully'
            })
    
    except Exception as e:
        logger.error(f'Error assigning {employee.full_name} to project: {e}')
        error_msg = 'Failed to assign employee to project'
        messages.error(request, error_msg)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': error_msg}, status=500)
    
    return redirect('employee:detail', pk=employee.pk)


@login_required
@verified_email_required
@role_required('OM', 'EG')
def export_employees_csv(request):
    """Export employees to CSV"""
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="employees_{date.today()}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Employee ID', 'First Name', 'Last Name', 'Email', 'Phone',
        'Role', 'Status', 'Hire Date', 'Contract End Date', 'Department',
        'Days Until Contract Expiry', 'Has User Account'
    ])
    
    # Write employee data
    employees = Employee.objects.select_related('user_profile').order_by('last_name', 'first_name')
    
    for employee in employees:
        writer.writerow([
            employee.employee_id,
            employee.first_name,
            employee.last_name,
            employee.email or '',
            employee.phone or '',
            employee.get_role_display(),
            employee.get_status_display(),
            employee.hire_date,
            employee.contract_end_date or '',
            employee.department or '',
            employee.days_until_contract_expiry or '',
            'Yes' if employee.user_profile else 'No'
        ])
    
    logger.info(f'Employee CSV export generated by {request.user}')
    return response


@login_required
@verified_email_required
@role_required('OM')  # Only Operations Managers
def send_contract_notifications(request):
    """Send contract expiry notifications for all employees"""
    
    if request.method == 'POST':
        # Get employees with expiring contracts
        expiring_employees = Employee.objects.expiring_soon(days=30)
        expired_employees = Employee.objects.expired()

        notifications_sent = 0
        failed_notifications = []

        # Send notifications for expiring contracts
        for employee in expiring_employees:
            if employee.send_contract_expiry_notification():
                employee.contract_expiry_notified = True
                employee.save(update_fields=['contract_expiry_notified'])
                notifications_sent += 1
            else:
                failed_notifications.append(employee.full_name)
                logger.error(f'Failed to send contract notification to {employee.full_name}')

        # Send notifications for expired contracts
        for employee in expired_employees:
            if employee.send_contract_expiry_notification():
                employee.contract_expiry_notified = True
                employee.save(update_fields=['contract_expiry_notified'])
                notifications_sent += 1
            else:
                failed_notifications.append(employee.full_name)
                logger.error(f'Failed to send contract notification to {employee.full_name}')

        if notifications_sent > 0:
            messages.success(request, f'Sent {notifications_sent} contract notifications.')
            logger.info(f'{notifications_sent} contract notifications sent by {request.user}')

        if failed_notifications:
            failed_names = ', '.join(failed_notifications)
            messages.error(request, f'Failed to send notifications to: {failed_names}')
            logger.error(f'Failed notifications for: {failed_names}')

        if notifications_sent == 0 and not failed_notifications:
            messages.info(request, 'No new notifications to send.')

        return redirect('employee:dashboard')
    
    # GET request - show confirmation page
    # Filter employees who haven't been notified yet
    expiring_employees = Employee.objects.expiring_soon(days=30).filter(contract_expiry_notified=False)
    expired_employees = Employee.objects.expired().filter(contract_expiry_notified=False)
    expiring_count = expiring_employees.count()
    expired_count = expired_employees.count()

    return render(request, 'employees/confirm_contract_notifications.html', {
        'expiring_employees': expiring_employees,
        'expired_employees': expired_employees,
        'expiring_count': expiring_count,
        'expired_count': expired_count,
        'total_notifications': expiring_count + expired_count
    })

@login_required
@verified_email_required
def employee_search_api(request):
    """API endpoint for employee search (for AJAX autocomplete)"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'results': []})
    
    employees = Employee.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(employee_id__icontains=query)
    ).active()[:10]
    
    results = []
    for employee in employees:
        results.append({
            'id': employee.pk,
            'text': f"{employee.full_name} ({employee.employee_id})",
            'employee_id': employee.employee_id,
            'role': employee.get_role_display(),
            'email': employee.email or ''
        })
    
    return JsonResponse({'results': results})


@login_required
@verified_email_required
def get_available_projects_api(request):
    """API endpoint to get available projects based on user role"""
    user_profile = request.user.userprofile
    user_role = user_profile.role
    
    # Filter projects based on user role (same logic as in detail view)
    if user_role == "PM":
        projects = ProjectProfile.objects.filter(project_manager=user_profile)
    elif user_role == "VO":
        try:
            user_email = user_profile.user.email
            if user_email:
                matching_clients = Client.objects.filter(email=user_email)
                if matching_clients.exists():
                    projects = ProjectProfile.objects.filter(client__in=matching_clients)
                else:
                    projects = ProjectProfile.objects.none()
            else:
                projects = ProjectProfile.objects.none()
        except Client.DoesNotExist:
            projects = ProjectProfile.objects.none()
    else:
        # For admin users or other roles
        projects = ProjectProfile.objects.all()
    
    # Filter only active projects
    projects = projects.filter(status='active').order_by('name')
    
    results = []
    for project in projects:
        results.append({
            'id': project.pk,
            'name': project.name,
            'description': project.description or '',
            'client': str(project.client) if project.client else ''
        })
    
    return JsonResponse({'projects': results})