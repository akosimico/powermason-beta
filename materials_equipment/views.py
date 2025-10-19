from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from authentication.models import UserProfile
from .models import (
    Material, MaterialPriceMonitoring, Equipment, Manpower,
    GeneralRequirement, ProjectMaterial, ProjectEquipment,
    ProjectManpower, ProjectGeneralRequirement
)
from .forms import (
    MaterialForm, MaterialPriceMonitoringForm, EquipmentForm,
    ManpowerForm, GeneralRequirementForm
)


# ===================
# MATERIALS VIEWS
# ===================

@login_required
def material_list(request):
    """List all materials"""
    return render(request, 'materials_equipment/material_list.html')


@login_required
def material_create(request):
    """Create new material"""
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Material created successfully'})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = MaterialForm()
    return render(request, 'materials_equipment/material_form.html', {'form': form})


@login_required
def material_edit(request, pk):
    """Edit material"""
    material = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Material updated successfully'})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = MaterialForm(instance=material)
    return render(request, 'materials_equipment/material_form.html', {
        'form': form,
        'material': material
    })


@login_required
def material_delete(request, pk):
    """Soft delete material"""
    material = get_object_or_404(Material, pk=pk)
    material.is_active = False
    material.save()
    return JsonResponse({'success': True, 'message': 'Material deleted successfully'})


# ===================
# EQUIPMENT VIEWS
# ===================

@login_required
def equipment_list(request):
    """List all equipment"""
    return render(request, 'materials_equipment/equipment_list.html')


@login_required
def equipment_create(request):
    """Create new equipment"""
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Equipment created successfully'})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)


@login_required
def equipment_edit(request, pk):
    """Edit equipment"""
    equipment = get_object_or_404(Equipment, pk=pk)
    if request.method == 'POST':
        form = EquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Equipment updated successfully'})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)


@login_required
def equipment_delete(request, pk):
    """Soft delete equipment"""
    equipment = get_object_or_404(Equipment, pk=pk)
    equipment.is_active = False
    equipment.save()
    return JsonResponse({'success': True, 'message': 'Equipment deleted successfully'})


# ===================
# PRICE MONITORING
# ===================

@login_required
def price_monitoring_dashboard(request):
    """Price monitoring dashboard"""
    return render(request, 'materials_equipment/price_monitoring.html')


@login_required
def price_monitoring_create(request):
    """Create new price monitoring record"""
    if request.method == 'POST':
        form = MaterialPriceMonitoringForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Price record created successfully'})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)


@login_required
def price_monitoring_edit(request, pk):
    """Edit price monitoring record"""
    price_record = get_object_or_404(MaterialPriceMonitoring, pk=pk)
    if request.method == 'POST':
        form = MaterialPriceMonitoringForm(request.POST, instance=price_record)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Price record updated successfully'})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)


@login_required
def price_monitoring_delete(request, pk):
    """Soft delete price monitoring record"""
    price_record = get_object_or_404(MaterialPriceMonitoring, pk=pk)
    price_record.is_active = False
    price_record.save()
    return JsonResponse({'success': True, 'message': 'Price record deleted successfully'})


# ===================
# API ENDPOINTS
# ===================

@require_http_methods(["GET"])
def api_material_list(request):
    """API endpoint for materials list"""
    materials = Material.objects.filter(is_active=True)

    # Search
    search = request.GET.get('search', '')
    if search:
        materials = materials.filter(
            Q(name__icontains=search) |
            Q(category__icontains=search)
        )

    # Filter by category
    category = request.GET.get('category', '')
    if category:
        materials = materials.filter(category=category)

    data = [{
        'id': m.id,
        'name': m.name,
        'unit': m.unit,
        'standard_price': float(m.standard_price),
        'category': m.category or '',
        'description': m.description or '',
        'latest_price': float(m.get_latest_price().price) if m.get_latest_price() else float(m.standard_price)
    } for m in materials]

    return JsonResponse({'materials': data, 'count': len(data)})


@require_http_methods(["GET"])
def api_material_detail(request, pk):
    """API endpoint for material details"""
    material = get_object_or_404(Material, pk=pk)

    # Get price history
    prices = MaterialPriceMonitoring.objects.filter(
        material=material,
        is_active=True
    ).order_by('-date')[:10]

    price_history = [{
        'date': p.date.isoformat(),
        'price': float(p.price),
        'supplier_type': p.get_supplier_type_display(),
        'supplier_name': p.supplier_name,
        'difference': float(p.price_difference_from_standard()),
        'percentage': float(p.price_difference_percentage())
    } for p in prices]

    return JsonResponse({
        'id': material.id,
        'name': material.name,
        'unit': material.unit,
        'standard_price': float(material.standard_price),
        'category': material.category or '',
        'description': material.description or '',
        'price_history': price_history
    })


@require_http_methods(["GET"])
def api_equipment_list(request):
    """API endpoint for equipment list"""
    equipment = Equipment.objects.filter(is_active=True)

    # Search
    search = request.GET.get('search', '')
    if search:
        equipment = equipment.filter(Q(name__icontains=search))

    data = [{
        'id': e.id,
        'name': e.name,
        'ownership_type': e.get_ownership_type_display(),
        'ownership_type_code': e.ownership_type,
        'rental_rate': float(e.rental_rate) if e.rental_rate else None,
        'purchase_price': float(e.purchase_price) if e.purchase_price else None,
        'description': e.description or ''
    } for e in equipment]

    return JsonResponse({'equipment': data, 'count': len(data)})


@require_http_methods(["GET"])
def api_equipment_detail(request, pk):
    """API endpoint for equipment details"""
    equipment = get_object_or_404(Equipment, pk=pk)

    return JsonResponse({
        'id': equipment.id,
        'name': equipment.name,
        'ownership_type': equipment.get_ownership_type_display(),
        'ownership_type_code': equipment.ownership_type,
        'rental_rate': float(equipment.rental_rate) if equipment.rental_rate else None,
        'purchase_price': float(equipment.purchase_price) if equipment.purchase_price else None,
        'description': equipment.description or ''
    })


@require_http_methods(["GET"])
def api_manpower_list(request):
    """API endpoint for manpower list"""
    manpower = Manpower.objects.filter(is_active=True)

    data = [{
        'id': m.id,
        'role': m.role,
        'daily_rate': float(m.daily_rate),
        'description': m.description or ''
    } for m in manpower]

    return JsonResponse({'manpower': data, 'count': len(data)})


@require_http_methods(["GET"])
def api_price_comparison(request):
    """API endpoint for price comparison data"""
    material_id = request.GET.get('material_id')

    if material_id:
        prices = MaterialPriceMonitoring.objects.filter(
            material_id=material_id,
            is_active=True
        ).order_by('-date')[:20]
    else:
        # Get latest prices for all materials
        prices = MaterialPriceMonitoring.objects.filter(
            is_active=True
        ).order_by('-date')[:50]

    # Group by supplier type
    regular_prices = []
    random_prices = []

    for p in prices:
        price_data = {
            'id': p.id,
            'date': p.date.isoformat(),
            'material': p.material.name,
            'price': float(p.price),
            'supplier': p.supplier_name,
            'supplier_type': p.supplier_type,
            'supplier_type_display': p.get_supplier_type_display(),
            'difference_pct': float(p.price_difference_percentage())
        }

        if p.supplier_type == 'REG':
            regular_prices.append(price_data)
        else:
            random_prices.append(price_data)

    return JsonResponse({
        'regular_suppliers': regular_prices,
        'random_suppliers': random_prices,
        'comparison': {
            'avg_regular': sum(p['price'] for p in regular_prices) / len(regular_prices) if regular_prices else 0,
            'avg_random': sum(p['price'] for p in random_prices) / len(random_prices) if random_prices else 0
        }
    })
