# ========================================
# RESOURCE ALLOCATION VIEWS
# Manage materials, equipment, and manpower for tasks
# ========================================

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from decimal import Decimal

from authentication.utils.decorators import verified_email_required, role_required
from authentication.utils.tokens import get_user_profile, verify_user_profile
from .models import ProjectTask, TaskMaterial, TaskEquipment, TaskManpower
from materials_equipment.models import ProjectMaterial, Equipment
from project_profiling.models import ProjectProfile


@login_required
@verified_email_required
@role_required('EG', 'OM', 'PM')
def task_resource_allocation(request, project_id, task_id):
    """
    View and manage resources (materials, equipment, manpower) for a task
    """
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    project = get_object_or_404(ProjectProfile, id=project_id)
    task = get_object_or_404(ProjectTask, id=task_id, project=project)

    # Check permissions
    if role == 'PM' and project.project_manager != verified_profile:
        return render(request, 'errors/403.html', status=403)

    # Get allocated resources
    allocated_materials = task.allocated_materials.select_related('material').all()
    allocated_equipment = task.allocated_equipment.select_related('equipment').all()
    allocated_manpower = task.allocated_manpower.all()

    # Calculate totals
    total_material_cost = sum(m.total_cost for m in allocated_materials)
    total_equipment_cost = sum(e.total_cost for e in allocated_equipment)
    total_manpower_cost = sum(m.total_cost for m in allocated_manpower)
    total_resource_cost = total_material_cost + total_equipment_cost + total_manpower_cost

    # Get available resources from project
    available_materials = ProjectMaterial.objects.filter(project=project)
    available_equipment = Equipment.objects.filter(
        project_equipment__project=project
    ).distinct()

    context = {
        'token': token,
        'role': role,
        'project': project,
        'task': task,
        'allocated_materials': allocated_materials,
        'allocated_equipment': allocated_equipment,
        'allocated_manpower': allocated_manpower,
        'total_material_cost': total_material_cost,
        'total_equipment_cost': total_equipment_cost,
        'total_manpower_cost': total_manpower_cost,
        'total_resource_cost': total_resource_cost,
        'available_materials': available_materials,
        'available_equipment': available_equipment,
        'labor_types': TaskManpower.LABOR_TYPE,
    }

    return render(request, 'scheduling/task_resource_allocation.html', context)


@login_required
@verified_email_required
@require_http_methods(["POST"])
@role_required('EG', 'OM')
def api_add_task_material(request, task_id):
    """Add material allocation to task"""
    import json

    try:
        task = get_object_or_404(ProjectTask, id=task_id)
        data = json.loads(request.body)

        material_id = data.get('material_id')
        quantity = data.get('quantity')
        unit_cost = data.get('unit_cost')
        notes = data.get('notes', '')

        # Validate
        if not all([material_id, quantity, unit_cost]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        material = get_object_or_404(ProjectMaterial, id=material_id)

        # Check if already allocated
        if TaskMaterial.objects.filter(task=task, material=material).exists():
            return JsonResponse({'error': 'Material already allocated to this task'}, status=400)

        # Create allocation
        allocation = TaskMaterial.objects.create(
            task=task,
            material=material,
            quantity_needed=Decimal(quantity),
            unit_cost=Decimal(unit_cost),
            notes=notes
        )

        return JsonResponse({
            'success': True,
            'message': 'Material allocated successfully',
            'allocation_id': allocation.id,
            'total_cost': float(allocation.total_cost)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@verified_email_required
@require_http_methods(["POST"])
@role_required('EG', 'OM')
def api_add_task_equipment(request, task_id):
    """Add equipment allocation to task"""
    import json

    try:
        task = get_object_or_404(ProjectTask, id=task_id)
        data = json.loads(request.body)

        equipment_id = data.get('equipment_id')
        allocation_type = data.get('allocation_type')
        quantity = data.get('quantity', 1)
        days_needed = data.get('days_needed')
        daily_rate = data.get('daily_rate')
        notes = data.get('notes', '')

        # Validate
        if not all([equipment_id, allocation_type, days_needed, daily_rate]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        equipment = get_object_or_404(Equipment, id=equipment_id)

        # Check if already allocated
        if TaskEquipment.objects.filter(task=task, equipment=equipment).exists():
            return JsonResponse({'error': 'Equipment already allocated to this task'}, status=400)

        # Create allocation
        allocation = TaskEquipment.objects.create(
            task=task,
            equipment=equipment,
            allocation_type=allocation_type,
            quantity=int(quantity),
            days_needed=int(days_needed),
            daily_rate=Decimal(daily_rate),
            notes=notes
        )

        return JsonResponse({
            'success': True,
            'message': 'Equipment allocated successfully',
            'allocation_id': allocation.id,
            'total_cost': float(allocation.total_cost)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@verified_email_required
@require_http_methods(["POST"])
@role_required('EG', 'OM')
def api_add_task_manpower(request, task_id):
    """Add manpower allocation to task"""
    import json

    try:
        task = get_object_or_404(ProjectTask, id=task_id)
        data = json.loads(request.body)

        labor_type = data.get('labor_type')
        description = data.get('description')
        number_of_workers = data.get('number_of_workers', 1)
        daily_rate = data.get('daily_rate')
        days_needed = data.get('days_needed')
        notes = data.get('notes', '')

        # Validate
        if not all([labor_type, description, daily_rate, days_needed]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Create allocation
        allocation = TaskManpower.objects.create(
            task=task,
            labor_type=labor_type,
            description=description,
            number_of_workers=int(number_of_workers),
            daily_rate=Decimal(daily_rate),
            days_needed=int(days_needed),
            notes=notes
        )

        return JsonResponse({
            'success': True,
            'message': 'Manpower allocated successfully',
            'allocation_id': allocation.id,
            'total_cost': float(allocation.total_cost),
            'total_manhours': float(allocation.total_manhours)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@verified_email_required
@require_http_methods(["DELETE"])
@role_required('EG', 'OM')
def api_delete_task_material(request, allocation_id):
    """Remove material allocation from task"""
    try:
        allocation = get_object_or_404(TaskMaterial, id=allocation_id)
        allocation.delete()

        return JsonResponse({
            'success': True,
            'message': 'Material allocation removed'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@verified_email_required
@require_http_methods(["DELETE"])
@role_required('EG', 'OM')
def api_delete_task_equipment(request, allocation_id):
    """Remove equipment allocation from task"""
    try:
        allocation = get_object_or_404(TaskEquipment, id=allocation_id)
        allocation.delete()

        return JsonResponse({
            'success': True,
            'message': 'Equipment allocation removed'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@verified_email_required
@require_http_methods(["DELETE"])
@role_required('EG', 'OM')
def api_delete_task_manpower(request, allocation_id):
    """Remove manpower allocation from task"""
    try:
        allocation = get_object_or_404(TaskManpower, id=allocation_id)
        allocation.delete()

        return JsonResponse({
            'success': True,
            'message': 'Manpower allocation removed'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@verified_email_required
@require_http_methods(["GET"])
def api_task_resource_summary(request, task_id):
    """Get resource summary for a task (for AJAX/charts)"""
    try:
        task = get_object_or_404(ProjectTask, id=task_id)

        # Materials
        materials = []
        for m in task.allocated_materials.select_related('material').all():
            materials.append({
                'id': m.id,
                'name': m.material.material_name,
                'quantity': float(m.quantity_needed),
                'unit': m.material.unit,
                'unit_cost': float(m.unit_cost),
                'total_cost': float(m.total_cost)
            })

        # Equipment
        equipment = []
        for e in task.allocated_equipment.select_related('equipment').all():
            equipment.append({
                'id': e.id,
                'name': e.equipment.name,
                'type': e.allocation_type,
                'quantity': e.quantity,
                'days': e.days_needed,
                'daily_rate': float(e.daily_rate),
                'total_cost': float(e.total_cost)
            })

        # Manpower
        manpower = []
        for m in task.allocated_manpower.all():
            manpower.append({
                'id': m.id,
                'type': m.get_labor_type_display(),
                'description': m.description,
                'workers': m.number_of_workers,
                'daily_rate': float(m.daily_rate),
                'days': m.days_needed,
                'total_cost': float(m.total_cost),
                'manhours': float(m.total_manhours)
            })

        # Totals
        total_material = sum(m['total_cost'] for m in materials)
        total_equipment = sum(e['total_cost'] for e in equipment)
        total_manpower = sum(m['total_cost'] for m in manpower)

        return JsonResponse({
            'success': True,
            'materials': materials,
            'equipment': equipment,
            'manpower': manpower,
            'totals': {
                'materials': total_material,
                'equipment': total_equipment,
                'manpower': total_manpower,
                'grand_total': total_material + total_equipment + total_manpower
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
