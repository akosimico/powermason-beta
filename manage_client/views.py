# manage_client/views.py - CONSOLIDATED VERSION
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from django.urls import reverse
import json
import os
from authentication.utils.tokens import get_user_profile, verify_user_profile
from authentication.templatetags.role_tags import has_role

from .models import Client, PROJECT_SOURCES
from project_profiling.models import ProjectProfile, ProjectType
from authentication.utils.decorators import verified_email_required, role_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re

from xero.xero_sync import sync_client_to_xero
from xero.xero_helpers import has_xero_connection

PHONE_REGEX = re.compile(r'^\+?\d{7,15}$') 

# ===== CLIENT MANAGEMENT VIEWS =====


@login_required
@role_required('OM', 'EG', 'superuser')
def client_management(request):
    print(f"DEBUG: xero_access_token in session: {bool(request.session.get('xero_access_token'))}")
    print(f"DEBUG: Session keys: {list(request.session.keys())}")
    
    # Handle AJAX request for stats only
    if request.GET.get('ajax_stats') == 'true':
        stats = {
            'total_clients': Client.objects.count(),
            'active_clients': Client.objects.filter(is_active=True).count(),
            'direct_clients': Client.objects.filter(client_type='DC').count(),
            'contractor_clients': Client.objects.filter(client_type='GC').count(),
        }
        return JsonResponse({'stats': stats})
    
    """
    Main page for managing clients with list, add, edit, delete functionality
    """
    context = get_client_management_context(request)
    search_query = request.GET.get('search', '')
    client_type_filter = request.GET.get('client_type', '')
    status_filter = request.GET.get('status', '')
    
    # Get user profile for role information
    profile = get_user_profile(request)
    if not profile:
        return redirect("unauthorized")
    
    role = profile.role
    
    # Get all clients with search functionality
    clients = Client.objects.all().order_by('company_name', 'contact_name')
    
    if search_query:
        clients = clients.filter(
            Q(company_name__icontains=search_query) |
            Q(contact_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    if 'form_data' in request.session:
        context['form_data'] = request.session.pop('form_data')
        context['show_add_modal'] = request.session.pop('show_add_modal', False)
        context['modal_mode'] = request.session.pop('modal_mode', 'add')
    
    # Filter by client type if specified
    if client_type_filter:
        clients = clients.filter(client_type=client_type_filter)
        
    if status_filter == 'active':
        clients = clients.filter(is_active=True)
    elif status_filter == 'inactive':
        clients = clients.filter(is_active=False)
    
    # Add project count for each client
    for client in clients:
        client.project_count = ProjectProfile.objects.filter(client=client).count()
    
    # Pagination
    paginator = Paginator(clients, 12)  # 12 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get statistics
    total_clients = Client.objects.count()
    active_clients = Client.objects.filter(is_active=True).count()
    direct_clients = Client.objects.filter(client_type='DC').count()
    contractor_clients = Client.objects.filter(client_type='GC').count()
    
    context.update({
        'page_obj': page_obj,
        'search_query': search_query,
        'client_type_filter': client_type_filter,
        'project_sources': PROJECT_SOURCES,
        'total_clients': total_clients,
        'active_clients': active_clients,
        'direct_clients': direct_clients,
        'contractor_clients': contractor_clients,
        'role': role,
        'has_xero_connection': has_xero_connection(request.user) if request.user.is_authenticated else False,
    })
    
    return render(request, 'manage-client/client_management.html', context)

@login_required
@role_required('OM', 'EG', 'superuser')
def create_project_for_client(request, client_id):
    """Bridge view to redirect to project creation with proper token/role."""
    client = get_object_or_404(Client, id=client_id)
    
    # Generate token for current user
    # Map client type to project type
    project_type = client.client_type  # 'DC' or 'GC'
    
    return redirect('project_create', project_type=project_type, client_id=client_id)

@login_required
@require_http_methods(["GET"])
def get_client_project_types(request, client_id):
    """Get project types for a specific client"""
    try:
        client = Client.objects.get(id=client_id)
        project_types = client.project_types.filter(is_active=True).values_list('id', flat=True)
        return JsonResponse({'project_types': list(project_types)})
    except Client.DoesNotExist:
        return JsonResponse({'error': 'Client not found'}, status=404)
    
@login_required
@role_required('OM', 'EG', 'superuser')
def add_client(request):
    """Add a new client (AJAX or classic)."""
    if request.method != 'POST':
        return redirect('client_management')

    # --- Form input ---
    company_name = request.POST.get('company_name', '').strip()
    contact_name = request.POST.get('contact_name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()
    address = request.POST.get('address', '').strip()
    city = request.POST.get('city', '').strip()
    state = request.POST.get('state', '').strip()
    zip_code = request.POST.get('zip_code', '').strip()
    client_type = request.POST.get('client_type', 'DC')
    notes = request.POST.get('notes', '').strip()
    is_active = request.POST.get('is_active') == 'on'
    project_types = request.POST.getlist('project_types')
    sync_to_xero = request.POST.get('sync_to_xero') == 'on'
    
    # Handle contract file upload
    contract_file = request.FILES.get('contract')

    # Preserve form data for errors
    form_data = {
        'company_name': company_name,
        'contact_name': contact_name,
        'email': email,
        'phone': phone,
        'address': address,
        'city': city,
        'state': state,
        'zip_code': zip_code,
        'client_type': client_type,
        'notes': notes,
        'is_active': is_active,
        'project_types': project_types,
        'sync_to_xero': sync_to_xero,
    }

    # --- Validation ---
    errors = []
    if not company_name:
        errors.append("Company name is required.")
    if not contact_name:
        errors.append("Contact name is required.")
    if not client_type or client_type not in [c[0] for c in PROJECT_SOURCES]:
        errors.append("Please select a valid client type.")
    if email:
        try:
            validate_email(email)
        except ValidationError:
            errors.append("Invalid email format.")
    if phone and not PHONE_REGEX.match(phone):
        errors.append("Phone number must be 7–15 digits (only numbers, optional +).")
    if Client.objects.filter(company_name__iexact=company_name).exists():
        errors.append("A client with this company name already exists.")

    # --- Contract file validation ---
    if contract_file:
        # Validate file type
        allowed_extensions = ['.pdf', '.doc', '.docx']
        file_extension = os.path.splitext(contract_file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            errors.append("Contract file must be PDF, DOC, or DOCX format.")
        
        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if contract_file.size > max_size:
            errors.append("Contract file size must be less than 10MB.")
        
        # Validate file name length
        if len(contract_file.name) > 255:
            errors.append("Contract file name is too long (max 255 characters).")

    # --- Return errors if any ---
    if errors:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": errors, "form_data": form_data}, status=400)

        for error in errors:
            messages.error(request, error)
        request.session['form_data'] = form_data
        request.session['show_add_modal'] = True
        request.session['modal_mode'] = 'add'
        return redirect('client_management')

    try:
        # --- Create client ---
        user_profile = request.user.userprofile
        client = Client.objects.create(
            company_name=company_name,
            contact_name=contact_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            client_type=client_type,
            notes=notes,
            is_active=is_active,
            created_by=user_profile,
            contract=contract_file,  # Add the contract file
        )

        # Save related project types
        if project_types:
            valid_project_types = ProjectType.objects.filter(id__in=project_types, is_active=True)
            client.project_types.set(valid_project_types)

        xero_sync_message = ""
        if sync_to_xero and has_xero_connection(request.user):
            sync_result = sync_client_to_xero(request, client)
            if sync_result['success']:
                xero_sync_message = " and synced to Xero"
            else:
                xero_sync_message = f" (Xero sync failed: {sync_result.get('message', 'Unknown error')})"
        
        client_type_display = dict(PROJECT_SOURCES).get(client_type, client_type)

        # --- Enriched client data for frontend ---
        project_count = ProjectProfile.objects.filter(client=client).count()
        project_types_list = list(client.project_types.values_list("name", flat=True))

        client_payload = {
            "id": client.id,
            "company_name": client.company_name,
            "contact_name": client.contact_name,
            "email": client.email,
            "phone": client.phone,
            "address": client.address,
            "city": client.city,
            "state": client.state,
            "zip_code": client.zip_code,
            "is_active": client.is_active,
            "client_type": client.client_type,
            "client_type_display": client_type_display,
            "project_count": project_count,
            "project_types": project_types_list,
            "can_delete": project_count == 0,
            "xero_contact_id": client.xero_contact_id,
            "xero_synced": bool(client.xero_contact_id),
            "contract_url": client.contract.url if client.contract else None,
            "contract_name": os.path.basename(client.contract.name) if client.contract else None,
        }

        success_message = f'{client_type_display} "{company_name}" created successfully{xero_sync_message}!'
        
        # --- AJAX return ---
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "success": True,
                "message": f'{client_type_display} "{company_name}" created successfully!',
                "client": client_payload,
            })

        # --- Non-AJAX return ---
        messages.success(request, f'{client_type_display} "{company_name}" created successfully.')
        return redirect('client_management')

    except Exception as e:
        # If there was an error and a file was uploaded, clean it up
        if contract_file and hasattr(contract_file, 'temporary_file_path'):
            try:
                os.unlink(contract_file.temporary_file_path())
            except (OSError, AttributeError):
                pass
        
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": [str(e)], "form_data": form_data}, status=500)

        messages.error(request, "Error creating client. Please check your data and try again.")
        context = get_client_management_context(request)
        context.update({'form_data': form_data, 'show_add_modal': True, 'modal_mode': 'add'})
        return render(request, 'manage-client/client_management.html', context)


def get_client_management_context(request):
    """
    Helper function to get all the context data needed for the client management page.
    You'll need to implement this based on your existing client_management view.
    """
    # Example - replace with your actual context logic:
    clients = Client.objects.all()  # or however you filter clients
    project_types = ProjectType.objects.filter(is_active=True)
    
    return {
        'clients': clients,
        'project_types': project_types,
        'PROJECT_SOURCES': PROJECT_SOURCES,
        # Add any other context variables your template needs
    }


@login_required
@role_required('OM', 'EG', 'superuser')
def edit_client(request, client_id):
    """Edit existing client"""
    client = get_object_or_404(Client, id=client_id)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    # -------------------
    # GET (AJAX modal load)
    # -------------------
    if request.method == "GET":
        if is_ajax:
            project_type_ids = list(client.project_types.values_list('id', flat=True))
            return JsonResponse({
                "success": True,
                "client": {
                    "id": client.id,
                    "company_name": client.company_name,
                    "contact_name": client.contact_name,
                    "email": client.email,
                    "phone": client.phone,
                    "address": client.address,
                    "city": client.city,
                    "state": client.state,
                    "zip_code": client.zip_code,
                    "client_type": client.client_type,
                    "notes": client.notes,
                    "is_active": client.is_active,
                    "project_type_ids": project_type_ids,
                    "xero_contact_id": client.xero_contact_id,
                    "contract_url": client.contract.url if client.contract else None,
                    "contract_name": os.path.basename(client.contract.name) if client.contract else None,
                }
            })
        # Normal GET → redirect to client management
        return redirect("client_management")

    # -------------------
    # POST (update client)
    # -------------------
    if request.method == "POST":
        company_name = request.POST.get("company_name", "").strip()
        contact_name = request.POST.get("contact_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        city = request.POST.get("city", "").strip()
        state = request.POST.get("state", "").strip()
        zip_code = request.POST.get("zip_code", "").strip()
        client_type = request.POST.get("client_type", client.client_type)
        notes = request.POST.get("notes", "").strip()
        is_active = request.POST.get("is_active") == "on"
        project_types = request.POST.getlist("project_types")
        should_sync_to_xero = request.POST.get("sync_to_xero") == "on"

        # -------------------
        # Validation
        # -------------------
        errors = []
        if not company_name:
            errors.append("Company name is required.")
        if not contact_name:
            errors.append("Contact name is required.")
        if not client_type or client_type not in [choice[0] for choice in PROJECT_SOURCES]:
            errors.append("Please select a valid client type.")
        if email:
            try:
                validate_email(email)
            except ValidationError:
                errors.append("Invalid email format.")
        if phone and not PHONE_REGEX.match(phone):
            errors.append("Phone number must be 7–15 digits (only numbers, optional +).")
        if Client.objects.filter(company_name__iexact=company_name).exclude(id=client_id).exists():
            errors.append("A client with this company name already exists.")

        if errors:
            if is_ajax:
                return JsonResponse({"success": False, "errors": errors}, status=400)
            for error in errors:
                messages.error(request, error)
            return render(request, "manage-client/client_management.html", {
                "page_obj": Client.objects.all(),
                "search_query": request.GET.get("search", ""),
                "edit_client_id": client.id,
            })

        # -------------------
        # Save changes (no contract handling)
        # -------------------
        try:
            client.company_name = company_name
            client.contact_name = contact_name
            client.email = email
            client.phone = phone
            client.address = address
            client.city = city
            client.state = state
            client.zip_code = zip_code
            client.client_type = client_type
            client.notes = notes
            client.is_active = is_active
            # Note: Contract field is not modified in edit mode
            client.save()

            if project_types:
                valid_project_types = ProjectType.objects.filter(id__in=project_types, is_active=True)
                client.project_types.set(valid_project_types)
            else:
                client.project_types.clear()

            # Handle Xero sync
            xero_synced = False
            xero_error = None
            if should_sync_to_xero:
                has_xero_connection = hasattr(request, "session") and request.session.get("xero_access_token")
                if has_xero_connection:
                    try:
                        success = client.sync_to_xero(request)
                        if success:
                            xero_synced = True
                        else:
                            xero_error = "Failed to sync to Xero"
                    except Exception as e:
                        xero_error = f"Xero sync error: {str(e)}"
                else:
                    xero_error = "Xero is not connected. Please connect to Xero first."

            client_type_display = dict(PROJECT_SOURCES).get(client_type, client_type)
            success_message = f'{client_type_display} "{company_name}" updated successfully.'
            
            if xero_synced:
                success_message += " Changes have been synced to Xero."
            elif xero_error:
                success_message += f" Warning: Xero sync failed - {xero_error}"

            # -------------------
            # Response
            # -------------------
            if is_ajax:
                project_count = ProjectProfile.objects.filter(client=client).count()
                project_type_names = [pt.name for pt in client.project_types.all()]
                can_delete = request.user.is_superuser or has_role(request.user, "OM")

                return JsonResponse({
                    "success": True,
                    "message": success_message,
                    "xero_synced": xero_synced,
                    "xero_error": xero_error,
                    "client": {
                        "id": client.id,
                        "company_name": client.company_name,
                        "contact_name": client.contact_name,
                        "email": client.email,
                        "phone": client.phone,
                        "city": client.city,
                        "state": client.state,
                        "is_active": client.is_active,
                        "client_type": client.client_type,
                        "client_type_display": client_type_display,
                        "project_count": project_count,
                        "project_types": project_type_names,
                        "can_delete": can_delete,
                        "xero_contact_id": client.xero_contact_id,
                        "xero_last_sync": client.xero_last_sync.isoformat() if client.xero_last_sync else None,
                        "contract_url": client.contract.url if client.contract else None,
                        "contract_name": os.path.basename(client.contract.name) if client.contract else None,
                    }
                })
            else:
                if xero_error:
                    messages.warning(request, f"Client updated but Xero sync failed: {xero_error}")
                messages.success(request, success_message)
                return redirect("client_management")

        except Exception as e:
            if is_ajax:
                return JsonResponse({"success": False, "errors": ["Error updating client. Please try again."]}, status=500)
            messages.error(request, "Error updating client. Please try again.")
            return redirect("client_management")

    # -------------------
    # Invalid methods
    # -------------------
    if is_ajax:
        return JsonResponse({"success": False, "errors": ["Invalid request method."]}, status=405)

    return redirect("client_management")

@login_required
@role_required('EG', 'superuser')
def delete_client(request, client_id):
    """Delete client (soft delete if has related projects)"""
    client = get_object_or_404(Client, id=client_id)
    
    if request.method == 'POST':
        project_count = ProjectProfile.objects.filter(client=client).count()
        
        if project_count > 0:
            client.is_active = False
            client.save()
            messages.warning(request, 
                f'Client "{client.company_name}" has been deactivated because they have {project_count} project(s). '
                'They will no longer appear in new project forms.')
        else:
            company_name = client.company_name
            client.delete()
            messages.success(request, f'Client "{company_name}" deleted successfully.')
    
    return redirect('client_management')



# ===== PROJECT TYPE MANAGEMENT VIEWS (MOVED FROM ADMINISTRATION) =====

@login_required
@role_required('OM', 'superuser')
def project_types_management(request):
    """
    Main page for managing project types with list, add, edit, delete functionality
    """
    # Get all project types with usage count
    project_types = ProjectType.objects.all().order_by('name')
    
    total_in_use = 0
    for pt in project_types:
        pt.usage_count = ProjectProfile.objects.filter(project_type=pt).count()
        total_in_use += pt.usage_count
    
    # Pagination
    paginator = Paginator(project_types, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Active types count
    active_types_count = ProjectType.objects.filter(is_active=True).count()
    
    context = {
        'page_obj': page_obj,
        'total_types': project_types.count(),
        'active_types': active_types_count,
        'total_in_use': total_in_use,   
    }
    
    return render(request, 'manage-client/project_types_management.html', context)


@login_required
@role_required('OM', 'EG', 'superuser')
def add_project_type(request):
    """Add new project type with cost configuration"""
    if request.method == 'POST':
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        code = request.POST.get('code', '').strip().upper()
        is_active = request.POST.get('is_active') == 'on'
        
        # Cost configuration fields
        base_cost_low_end = request.POST.get('base_cost_low_end')
        base_cost_mid_range = request.POST.get('base_cost_mid_range')
        base_cost_high_end = request.POST.get('base_cost_high_end')
        
        # Cost breakdown percentages
        materials_percentage = request.POST.get('materials_percentage', '40.00')
        labor_percentage = request.POST.get('labor_percentage', '30.00')
        equipment_percentage = request.POST.get('equipment_percentage', '10.00')
        permits_percentage = request.POST.get('permits_percentage', '5.00')
        contingency_percentage = request.POST.get('contingency_percentage', '10.00')
        overhead_percentage = request.POST.get('overhead_percentage', '5.00')
        
        # Validation
        if not name:
            error_msg = 'Project type name is required.'
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
            return redirect('manage_client:project_types_management')
        
        if not code:
            # Auto-generate code from name
            code = ''.join([word[0].upper() for word in name.split() if word])[:10]
        
        # Validate percentages add up to 100%
        try:
            total_percentage = (
                float(materials_percentage or 0) + 
                float(labor_percentage or 0) + 
                float(equipment_percentage or 0) + 
                float(permits_percentage or 0) + 
                float(contingency_percentage or 0) + 
                float(overhead_percentage or 0)
            )
            if abs(total_percentage - 100) > 0.01:
                error_msg = f'Cost breakdown percentages must add up to 100%. Current total: {total_percentage:.2f}%'
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_msg})
                messages.error(request, error_msg)
                return redirect('manage_client:project_types_management')
        except (ValueError, TypeError):
            error_msg = 'Invalid percentage values.'
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
            return redirect('manage_client:project_types_management')
        
        try:
            user_profile = request.user.userprofile
            project_type = ProjectType.objects.create(
                name=name,
                description=description,
                code=code,
                is_active=is_active,
                created_by=user_profile,
                # Cost configuration
                base_cost_low_end=base_cost_low_end if base_cost_low_end else None,
                base_cost_mid_range=base_cost_mid_range if base_cost_mid_range else None,
                base_cost_high_end=base_cost_high_end if base_cost_high_end else None,
                # Cost breakdown
                materials_percentage=materials_percentage,
                labor_percentage=labor_percentage,
                equipment_percentage=equipment_percentage,
                permits_percentage=permits_percentage,
                contingency_percentage=contingency_percentage,
                overhead_percentage=overhead_percentage,
            )
            success_msg = f'Project type "{name}" created successfully.'
            if is_ajax:
                return JsonResponse({
                    'success': True, 
                    'message': success_msg,
                    'project_type': {
                        'id': project_type.id,
                        'name': project_type.name,
                        'code': project_type.code,
                        'description': project_type.description
                    }
                })
            messages.success(request, success_msg)
        except IntegrityError:
            error_msg = 'A project type with this name or code already exists.'
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
        
        return redirect('manage_client:project_types_management')
    
    return redirect('manage_client:project_types_management')


@login_required
@role_required('OM','EG', 'superuser')
def edit_project_type(request, type_id):
    """Edit existing project type with cost configuration"""
    project_type = get_object_or_404(ProjectType, id=type_id)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        code = request.POST.get('code', '').strip().upper()
        is_active = request.POST.get('is_active') == 'on'
        
        # Cost configuration fields
        base_cost_low_end = request.POST.get('base_cost_low_end')
        base_cost_mid_range = request.POST.get('base_cost_mid_range')
        base_cost_high_end = request.POST.get('base_cost_high_end')
        
        # Cost breakdown percentages
        materials_percentage = request.POST.get('materials_percentage', '40.00')
        labor_percentage = request.POST.get('labor_percentage', '30.00')
        equipment_percentage = request.POST.get('equipment_percentage', '10.00')
        permits_percentage = request.POST.get('permits_percentage', '5.00')
        contingency_percentage = request.POST.get('contingency_percentage', '10.00')
        overhead_percentage = request.POST.get('overhead_percentage', '5.00')
        
        # Validation
        if not name:
            messages.error(request, 'Project type name is required.')
            return redirect('manage_client:project_types_management')
        
        if not code:
            # Auto-generate code from name
            code = ''.join([word[0].upper() for word in name.split() if word])[:10]
        
        # Check for duplicates (excluding current record)
        if ProjectType.objects.filter(name=name).exclude(id=type_id).exists():
            messages.error(request, 'A project type with this name already exists.')
            return redirect('manage_client:project_types_management')
            
        if ProjectType.objects.filter(code=code).exclude(id=type_id).exists():
            messages.error(request, 'A project type with this code already exists.')
            return redirect('manage_client:project_types_management')
        
        # Validate percentages add up to 100%
        try:
            total_percentage = (
                float(materials_percentage or 0) + 
                float(labor_percentage or 0) + 
                float(equipment_percentage or 0) + 
                float(permits_percentage or 0) + 
                float(contingency_percentage or 0) + 
                float(overhead_percentage or 0)
            )
            if abs(total_percentage - 100) > 0.01:
                messages.error(request, f'Cost breakdown percentages must add up to 100%. Current total: {total_percentage:.2f}%')
                return redirect('manage_client:project_types_management')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid percentage values.')
            return redirect('manage_client:project_types_management')
        
        try:
            project_type.name = name
            project_type.description = description
            project_type.code = code
            project_type.is_active = is_active
            # Cost configuration
            project_type.base_cost_low_end = base_cost_low_end if base_cost_low_end else None
            project_type.base_cost_mid_range = base_cost_mid_range if base_cost_mid_range else None
            project_type.base_cost_high_end = base_cost_high_end if base_cost_high_end else None
            # Cost breakdown
            project_type.materials_percentage = materials_percentage
            project_type.labor_percentage = labor_percentage
            project_type.equipment_percentage = equipment_percentage
            project_type.permits_percentage = permits_percentage
            project_type.contingency_percentage = contingency_percentage
            project_type.overhead_percentage = overhead_percentage
            project_type.save()
            
            messages.success(request, f'Project type "{name}" updated successfully.')
        except IntegrityError:
            messages.error(request, 'Error updating project type. Please try again.')
        
        return redirect('manage_client:project_types_management')
    
    # GET request - redirect back to management (modal system handles data fetching)
    return redirect('project_types_management')


@login_required
@role_required('OM', 'EG','superuser')
def delete_project_type(request, type_id):
    """Delete project type (soft delete if has related projects)"""
    project_type = get_object_or_404(ProjectType, id=type_id)
    
    if request.method == 'POST':
        usage_count = ProjectProfile.objects.filter(project_type=project_type).count()
        
        if usage_count > 0:
            project_type.is_active = False
            project_type.save()
            messages.warning(request, 
                f'Project type "{project_type.name}" has been deactivated because it\'s used in {usage_count} project(s). '
                'It will no longer appear in new project forms.')
        else:
            project_type_name = project_type.name
            project_type.delete()
            messages.success(request, f'Project type "{project_type_name}" deleted successfully.')
    
    return redirect('project_types_management')


# ===== API ENDPOINTS =====

@login_required
@role_required('OM', 'EG', 'superuser')
@require_http_methods(["GET"])
def get_client(request, client_id):
    """AJAX endpoint to get client details for editing"""
    try:
        client = Client.objects.get(pk=client_id)
        data = {
            "company_name": client.company_name,
            "contact_name": client.contact_name,
            "email": client.email,
            "phone": client.phone,
            "address": client.address,
            "city": client.city,
            "state": client.state,
            "zip_code": client.zip_code,
            "client_type": client.client_type,
            "notes": client.notes,
            "is_active": client.is_active,
            "project_types": list(client.project_types.values_list('id', flat=True)),
            'xero_contact_id': client.xero_contact_id,
            'xero_last_sync': client.xero_last_sync.isoformat() if client.xero_last_sync else None,
            
        }
        return JsonResponse(data)
    except Client.DoesNotExist:
        raise Http404("Client not found")


@login_required
@role_required('OM', 'superuser')
@require_http_methods(["GET"])
def get_project_type(request, type_id):
    """AJAX endpoint to get project type details for editing"""
    try:
        project_type = ProjectType.objects.get(id=type_id)
        data = {
            'id': project_type.id,
            'name': project_type.name,
            'description': project_type.description,
            'code': project_type.code,
            'is_active': project_type.is_active,
            'base_cost_low_end': float(project_type.base_cost_low_end) if project_type.base_cost_low_end else None,
            'base_cost_mid_range': float(project_type.base_cost_mid_range) if project_type.base_cost_mid_range else None,
            'base_cost_high_end': float(project_type.base_cost_high_end) if project_type.base_cost_high_end else None,
            'materials_percentage': float(project_type.materials_percentage),
            'labor_percentage': float(project_type.labor_percentage),
            'equipment_percentage': float(project_type.equipment_percentage),
            'permits_percentage': float(project_type.permits_percentage),
            'contingency_percentage': float(project_type.contingency_percentage),
            'overhead_percentage': float(project_type.overhead_percentage),
        }
        return JsonResponse(data)
    except ProjectType.DoesNotExist:
        return JsonResponse({'error': 'Project type not found'}, status=404)


@login_required
@require_http_methods(["GET"])
def get_available_project_types(request):
    """Get all active project types"""
    project_types = ProjectType.objects.filter(is_active=True).order_by('name')
    
    data = [{
        'id': pt.id,
        'name': pt.name,
        'code': pt.code,
        'description': pt.description,
        'usage_count': pt.get_usage_count()
    } for pt in project_types]
    
    return JsonResponse({'project_types': data})


@login_required
@require_http_methods(["GET"])
def get_active_clients(request):
    """API endpoint to get active clients for project forms"""
    client_type = request.GET.get('client_type', '')
    
    clients_query = Client.objects.filter(is_active=True).order_by('company_name')
    
    if client_type and client_type in [choice[0] for choice in PROJECT_SOURCES]:
        clients_query = clients_query.filter(client_type=client_type)
    
    clients = clients_query
    data = [{
        'id': client.id,
        'company_name': client.company_name,
        'contact_name': client.contact_name,
        'email': client.email,
        'phone': client.phone,
        'address': client.address,
        'city': client.city,
        'state': client.state,
        'zip_code': client.zip_code,
        'client_type': client.client_type,
        'client_type_display': client.get_client_type_display(),
        'full_address': f"{client.address}, {client.city}, {client.state} {client.zip_code}".strip(', ')
    } for client in clients]
    
    return JsonResponse({'clients': data})


@login_required
@require_http_methods(["GET"])
def search_clients(request):
    """AJAX endpoint for client search"""
    query = request.GET.get('q', '').strip()
    client_type = request.GET.get('client_type', '')
    
    if len(query) < 2:
        return JsonResponse({'clients': []})
    
    clients_query = Client.objects.filter(
        Q(company_name__icontains=query) |
        Q(contact_name__icontains=query),
        is_active=True
    )
    
    if client_type and client_type in [choice[0] for choice in PROJECT_SOURCES]:
        clients_query = clients_query.filter(client_type=client_type)
    
    clients = clients_query.order_by('company_name')[:10]
    
    data = [{
        'id': client.id,
        'company_name': client.company_name,
        'contact_name': client.contact_name,
        'email': client.email,
        'phone': client.phone,
        'client_type': client.client_type,
        'client_type_display': client.get_client_type_display(),
        'display_name': f"{client.company_name} ({client.contact_name}) - {client.get_client_type_display()}"
    } for client in clients]
    
    return JsonResponse({'clients': data})


@login_required
@require_http_methods(["GET"])
def get_client_types(request):
    """API endpoint to get available client types"""
    data = [{'value': choice[0], 'label': choice[1]} for choice in PROJECT_SOURCES]
    return JsonResponse({'client_types': data})


@login_required
@require_http_methods(["GET"])
def get_active_project_types(request):
    """API endpoint to get active project types for project forms"""
    project_types = ProjectType.objects.filter(is_active=True).order_by('name')
    data = [{
        'id': pt.id,
        'name': pt.name,
        'code': pt.code,
        'description': pt.description
    } for pt in project_types]
    
    return JsonResponse({'project_types': data})


@login_required
@role_required('OM', 'EG', 'superuser')
@require_http_methods(["POST"])
def create_project_type_from_client(request):
    """Create a new project type from the client management interface"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            description = data.get('description', '').strip()
            code = data.get('code', '').strip().upper()
            
            # Auto-generate code if not provided
            if not code:
                code = ''.join([word[0].upper() for word in name.split() if word])[:10]
            
            # Validation
            if not name:
                return JsonResponse({'success': False, 'error': 'Project type name is required.'})
            
            # Check for duplicates
            if ProjectType.objects.filter(name__iexact=name).exists():
                return JsonResponse({'success': False, 'error': 'A project type with this name already exists.'})
            
            if ProjectType.objects.filter(code__iexact=code).exists():
                return JsonResponse({'success': False, 'error': 'A project type with this code already exists.'})
            
            # Create the project type
            user_profile = request.user.userprofile
            project_type = ProjectType.objects.create(
                name=name,
                description=description,
                code=code,
                is_active=True,
                created_by=user_profile
            )
            
            # Add Django success message
            messages.success(request, f'Project type "{project_type.name}" created successfully.')
            
            return JsonResponse({
                'success': True,
                'project_type': {
                    'id': project_type.id,
                    'name': project_type.name,
                    'code': project_type.code,
                    'description': project_type.description,
                }
                # Removed redirect_url so it stays in the modal
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

def get_client_projects(request, client_id):
    try:
        client = Client.objects.get(id=client_id)
        projects = ProjectProfile.objects.filter(client=client).order_by('-created_at')
        
        projects_data = []
        for project in projects:
            projects_data.append({
                'id': project.id,
                'project_id': project.project_id,
                'project_name': project.project_name,
                'description': project.description,
                'status': project.status,
                'location': project.location,
                'start_date': project.start_date.isoformat() if project.start_date else None,
                'target_completion_date': project.target_completion_date.isoformat() if project.target_completion_date else None,
                'estimated_cost': float(project.estimated_cost) if project.estimated_cost else None,
                'project_type': project.project_type.name if project.project_type else None,
            })
        
        return JsonResponse({
            'projects': projects_data,
            'total_count': len(projects_data)
        })
    except Client.DoesNotExist:
        return JsonResponse({'error': 'Client not found'}, status=404)
    
def clients_by_type(request):
    client_type = request.GET.get('client_type')
    if client_type:
        clients = Client.objects.filter(client_type=client_type, is_active=True)
    else:
        clients = Client.objects.filter(is_active=True)
    
    client_data = [
        {
            'id': client.id,
            'company_name': client.company_name,
            'client_type': client.client_type
        }
        for client in clients
    ]
    
    return JsonResponse({'clients': client_data})

def sync_client_manual(request, client_id):
    """Manually sync a single client to Xero"""
    if not request.session.get('xero_access_token'):
        return JsonResponse({'success': False, 'error': 'Not connected to Xero'})
    
    try:
        client = Client.objects.get(id=client_id)
        result = sync_client_to_xero(request, client)
        return JsonResponse(result)
    except Client.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Client not found'})


@login_required
@role_required('OM', 'EG', 'superuser')
@require_http_methods(["POST"])
def add_client_ajax(request):
    """AJAX endpoint to add a new client"""
    try:
        # Get form data
        company_name = request.POST.get('company_name', '').strip()
        contact_name = request.POST.get('contact_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        zip_code = request.POST.get('zip_code', '').strip()
        client_type = request.POST.get('client_type', 'DC').strip()
        project_types = request.POST.getlist('project_types')
        
        # Validate required fields
        if not company_name:
            return JsonResponse({'success': False, 'message': 'Company name is required'})
        if not contact_name:
            return JsonResponse({'success': False, 'message': 'Contact name is required'})
        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required'})
        if not phone:
            return JsonResponse({'success': False, 'message': 'Phone number is required'})
        
        # Validate that at least one project type is selected
        if not project_types:
            return JsonResponse({'success': False, 'message': 'At least one project type must be selected'})
        
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({'success': False, 'message': 'Invalid email format'})
        
        # Validate phone if provided
        if phone and not PHONE_REGEX.match(phone):
            return JsonResponse({'success': False, 'message': 'Invalid phone number format'})
        
        # Check if client with same email already exists
        if Client.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'A client with this email already exists'})
        
        # Create new client
        client = Client.objects.create(
            company_name=company_name,
            contact_name=contact_name,
            email=email,
            phone=phone,  # Phone is now required, so no need for fallback
            address=address or '',
            city=city or '',
            state=state or '',
            zip_code=zip_code or '',
            client_type=client_type,
            is_active=True
        )
        
        # Assign project types to client
        if project_types:
            valid_project_types = ProjectType.objects.filter(id__in=project_types, is_active=True)
            client.project_types.set(valid_project_types)
        
        # Return client data
        return JsonResponse({
            'success': True,
            'message': 'Client added successfully',
            'client': {
                'id': client.id,
                'company_name': client.company_name,
                'contact_name': client.contact_name,
                'email': client.email,
                'phone': client.phone or '',
                'address': client.address or '',
                'city': client.city or '',
                'state': client.state or '',
                'zip_code': client.zip_code or '',
                'client_type': client.client_type or ''
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error adding client: {str(e)}'})


@login_required
def get_project_types(request):
    """Get all active project types for AJAX requests"""
    try:
        project_types = ProjectType.objects.filter(is_active=True).order_by('name')
        data = []
        for pt in project_types:
            data.append({
                'id': pt.id,
                'name': pt.name,
                'code': pt.code,
                'description': pt.description,
            })
        return JsonResponse({'success': True, 'project_types': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_client_project_types(request, client_id):
    """Get project types for a specific client"""
    try:
        client = get_object_or_404(Client, id=client_id)
        project_types = client.project_types.filter(is_active=True).order_by('name')
        data = []
        for pt in project_types:
            data.append({
                'id': pt.id,
                'name': pt.name,
                'code': pt.code,
                'description': pt.description,
            })
        return JsonResponse({'success': True, 'project_types': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})