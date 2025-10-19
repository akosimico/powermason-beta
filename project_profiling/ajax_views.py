"""
AJAX Views for seamless navigation
Provides AJAX endpoints for smooth module transitions
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Q
from authentication.utils.decorators import verified_email_required
from .models import ProjectProfile, ProjectStaging, Client
# Removed get_user_projects import - will create inline
import json


def get_user_projects(user):
    """Get projects accessible to the user based on their role"""
    if user.is_superuser:
        return ProjectProfile.objects.all()
    
    # Get user's employee profile
    try:
        employee_profile = user.employee_profile
    except:
        return ProjectProfile.objects.none()
    
    # Filter projects based on user role and assignments
    if employee_profile.role in ['PM', 'EG', 'OM']:
        # Project managers, engineers, and operations managers can see all projects
        return ProjectProfile.objects.all()
    else:
        # Other roles can only see projects they're assigned to
        return ProjectProfile.objects.filter(
            Q(project_manager=employee_profile) |
            Q(project_in_charge=employee_profile) |
            Q(safety_officer=employee_profile) |
            Q(quality_assurance_officer=employee_profile) |
            Q(quality_officer=employee_profile) |
            Q(foreman=employee_profile)
        )


class AjaxViewMixin:
    """Mixin for AJAX views that provides common functionality"""
    
    def dispatch(self, request, *args, **kwargs):
        # Check if this is an AJAX request
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'AJAX request required'}, status=400)
        
        return super().dispatch(request, *args, **kwargs)
    
    def render_ajax_response(self, template_name, context=None):
        """Render template for AJAX response"""
        if context is None:
            context = {}
        
        # Add common context variables
        context.update({
            'is_ajax': True,
            'user': self.request.user,
        })
        
        return render(self.request, template_name, context)


@method_decorator([login_required, verified_email_required], name='dispatch')
class ProjectListAjaxView(AjaxViewMixin, View):
    """AJAX view for project list"""
    
    def get(self, request):
        try:
            # Get user's projects
            projects = get_user_projects(request.user)
            
            # Get filter parameters
            project_type = request.GET.get('type', '')
            status = request.GET.get('status', '')
            search = request.GET.get('search', '')
            
            # Apply filters
            if project_type:
                projects = projects.filter(project_source=project_type)
            
            if status:
                projects = projects.filter(status=status)
            
            if search:
                projects = projects.filter(
                    project_name__icontains=search
                ) | projects.filter(
                    client__company_name__icontains=search
                )
            
            context = {
                'projects': projects,
                'project_type': project_type,
                'status': status,
                'search': search,
            }
            
            return self.render_ajax_response('project_profiling/project_list_ajax.html', context)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator([login_required, verified_email_required], name='dispatch')
class ProjectDetailAjaxView(AjaxViewMixin, View):
    """AJAX view for project detail"""
    
    def get(self, request, project_id):
        try:
            project = ProjectProfile.objects.get(id=project_id)
            
            # Check if user has access to this project
            if not self.has_access(request.user, project):
                return JsonResponse({'error': 'Access denied'}, status=403)
            
            context = {
                'project': project,
            }
            
            return self.render_ajax_response('project_profiling/project_detail_ajax.html', context)
            
        except ProjectProfile.DoesNotExist:
            return JsonResponse({'error': 'Project not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def has_access(self, user, project):
        """Check if user has access to the project"""
        # Add your access control logic here
        return True


@method_decorator([login_required, verified_email_required], name='dispatch')
class ClientListAjaxView(AjaxViewMixin, View):
    """AJAX view for client list"""
    
    def get(self, request):
        try:
            clients = Client.objects.filter(is_active=True).order_by('company_name')
            
            # Get filter parameters
            search = request.GET.get('search', '')
            client_type = request.GET.get('type', '')
            
            # Apply filters
            if search:
                clients = clients.filter(
                    company_name__icontains=search
                ) | clients.filter(
                    contact_person__icontains=search
                )
            
            if client_type:
                clients = clients.filter(client_type=client_type)
            
            context = {
                'clients': clients,
                'search': search,
                'client_type': client_type,
            }
            
            return self.render_ajax_response('manage_client/client_list_ajax.html', context)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator([login_required, verified_email_required], name='dispatch')
class DashboardAjaxView(AjaxViewMixin, View):
    """AJAX view for dashboard"""
    
    def get(self, request):
        try:
            # Get user's projects for dashboard
            projects = get_user_projects(request.user)
            
            # Get dashboard data
            total_projects = projects.count()
            active_projects = projects.filter(status='ACTIVE').count()
            completed_projects = projects.filter(status='COMPLETED').count()
            pending_projects = projects.filter(status='PENDING').count()
            
            # Get recent projects
            recent_projects = projects.order_by('-created_at')[:5]
            
            context = {
                'total_projects': total_projects,
                'active_projects': active_projects,
                'completed_projects': completed_projects,
                'pending_projects': pending_projects,
                'recent_projects': recent_projects,
            }
            
            return self.render_ajax_response('dashboard_ajax.html', context)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator([login_required, verified_email_required], name='dispatch')
class EmployeeListAjaxView(AjaxViewMixin, View):
    """AJAX view for employee list"""
    
    def get(self, request):
        try:
            from employees.models import Employee
            
            employees = Employee.objects.filter(is_active=True).order_by('first_name', 'last_name')
            
            # Get filter parameters
            search = request.GET.get('search', '')
            role = request.GET.get('role', '')
            department = request.GET.get('department', '')
            
            # Apply filters
            if search:
                employees = employees.filter(
                    first_name__icontains=search
                ) | employees.filter(
                    last_name__icontains=search
                ) | employees.filter(
                    email__icontains=search
                )
            
            if role:
                employees = employees.filter(role=role)
            
            if department:
                employees = employees.filter(department=department)
            
            context = {
                'employees': employees,
                'search': search,
                'role': role,
                'department': department,
            }
            
            return self.render_ajax_response('employees/employee_list_ajax.html', context)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator([login_required, verified_email_required], name='dispatch')
class DocumentLibraryAjaxView(AjaxViewMixin, View):
    """AJAX view for document library"""
    
    def get(self, request):
        try:
            from .models import ProjectDocument
            
            documents = ProjectDocument.objects.filter(is_archived=False).order_by('-uploaded_at')
            
            # Get filter parameters
            search = request.GET.get('search', '')
            document_type = request.GET.get('type', '')
            project_id = request.GET.get('project', '')
            
            # Apply filters
            if search:
                documents = documents.filter(
                    name__icontains=search
                ) | documents.filter(
                    description__icontains=search
                )
            
            if document_type:
                documents = documents.filter(document_type=document_type)
            
            if project_id:
                documents = documents.filter(project_id=project_id)
            
            context = {
                'documents': documents,
                'search': search,
                'document_type': document_type,
                'project_id': project_id,
            }
            
            return self.render_ajax_response('project_profiling/document_library_ajax.html', context)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator([login_required, verified_email_required], name='dispatch')
class CostDashboardAjaxView(AjaxViewMixin, View):
    """AJAX view for cost dashboard"""
    
    def get(self, request):
        try:
            # Get user's projects for cost analysis
            projects = get_user_projects(request.user)
            
            # Get cost data
            total_budget = sum(project.estimated_cost or 0 for project in projects)
            total_spent = sum(project.actual_cost or 0 for project in projects)
            
            # Get projects by status for cost analysis
            active_projects = projects.filter(status='ACTIVE')
            completed_projects = projects.filter(status='COMPLETED')
            
            context = {
                'total_budget': total_budget,
                'total_spent': total_spent,
                'active_projects': active_projects,
                'completed_projects': completed_projects,
            }
            
            return self.render_ajax_response('project_profiling/cost_dashboard_ajax.html', context)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# Function-based AJAX views for simpler endpoints
@login_required
@verified_email_required
@require_http_methods(["GET"])
def ajax_navigation_handler(request):
    """Generic AJAX navigation handler"""
    try:
        # Get the requested module/page
        module = request.GET.get('module', '')
        page = request.GET.get('page', '')
        
        # Route to appropriate view based on module
        if module == 'projects':
            if page == 'list':
                return ProjectListAjaxView.as_view()(request)
            elif page == 'dashboard':
                return DashboardAjaxView.as_view()(request)
        elif module == 'clients':
            if page == 'list':
                return ClientListAjaxView.as_view()(request)
        elif module == 'employees':
            if page == 'list':
                return EmployeeListAjaxView.as_view()(request)
        elif module == 'documents':
            if page == 'library':
                return DocumentLibraryAjaxView.as_view()(request)
        elif module == 'costs':
            if page == 'dashboard':
                return CostDashboardAjaxView.as_view()(request)
        
        return JsonResponse({'error': 'Invalid module or page'}, status=400)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@verified_email_required
@require_http_methods(["GET"])
def ajax_search_handler(request):
    """Generic AJAX search handler"""
    try:
        query = request.GET.get('q', '')
        type = request.GET.get('type', 'all')
        
        results = {
            'projects': [],
            'clients': [],
            'employees': [],
            'documents': []
        }
        
        if query:
            # Search projects
            if type in ['all', 'projects']:
                projects = ProjectProfile.objects.filter(
                    project_name__icontains=query
                )[:5]
                results['projects'] = [
                    {
                        'id': p.id,
                        'name': p.project_name,
                        'type': p.project_source,
                        'status': p.status,
                        'url': f'/projects/view/{p.project_source}/{p.id}/'
                    }
                    for p in projects
                ]
            
            # Search clients
            if type in ['all', 'clients']:
                clients = Client.objects.filter(
                    company_name__icontains=query
                )[:5]
                results['clients'] = [
                    {
                        'id': c.id,
                        'name': c.company_name,
                        'type': c.client_type,
                        'url': f'/clients/{c.id}/'
                    }
                    for c in clients
                ]
            
            # Search employees
            if type in ['all', 'employees']:
                from employees.models import Employee
                employees = Employee.objects.filter(
                    first_name__icontains=query
                ) | Employee.objects.filter(
                    last_name__icontains=query
                )[:5]
                results['employees'] = [
                    {
                        'id': e.id,
                        'name': f"{e.first_name} {e.last_name}",
                        'role': e.role,
                        'url': f'/employees/{e.id}/'
                    }
                    for e in employees
                ]
        
        return JsonResponse({'results': results, 'query': query})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
