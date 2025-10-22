from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Avg
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
    """API endpoint for materials list with enhanced filtering and pagination"""
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
    
    # Filter by source
    source = request.GET.get('source', '')
    if source:
        materials = materials.filter(source=source)
    
    # Filter by project
    project_id = request.GET.get('project', '')
    if project_id:
        # Get materials that have price records for this project
        project_material_ids = MaterialPriceMonitoring.objects.filter(
            project_id=project_id
        ).values_list('material_id', flat=True)
        materials = materials.filter(id__in=project_material_ids)
    
    # Pagination
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    start = (page - 1) * page_size
    end = start + page_size
    
    total_count = materials.count()
    materials = materials[start:end]

    data = []
    for m in materials:
        latest_price = m.get_latest_price()
        latest_price_value = float(latest_price.price) if latest_price else float(m.standard_price)
        
        # Calculate variance from standard price
        variance = latest_price_value - float(m.standard_price)
        variance_percentage = (variance / float(m.standard_price) * 100) if m.standard_price > 0 else 0
        
        # Get project-specific price records
        project_prices = MaterialPriceMonitoring.objects.filter(material=m)
        boq_price = project_prices.filter(supplier_type='BOQ').first()
        quotation_price = project_prices.filter(supplier_type='QUOTATION').first()
        
        data.append({
            'id': m.id,
            'name': m.name,
            'unit': m.unit,
            'standard_price': float(m.standard_price),
            'category': m.category or '',
            'description': m.description or '',
            'source': m.source or '',
            'latest_price': latest_price_value,
            'variance': variance,
            'variance_percentage': variance_percentage,
            'boq_price': float(boq_price.price) if boq_price else None,
            'quotation_price': float(quotation_price.price) if quotation_price else None,
            'project_count': project_prices.values('project').distinct().count()
        })

    return JsonResponse({
        'materials': data, 
        'count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size
    })


@require_http_methods(["GET"])
def api_price_monitoring_list(request):
    """API endpoint for price monitoring with enhanced filtering and pagination"""
    prices = MaterialPriceMonitoring.objects.all()
    
    # Filter by supplier type
    supplier_type = request.GET.get('supplier_type', '')
    if supplier_type:
        prices = prices.filter(supplier_type=supplier_type)
    
    # Filter by project
    project_id = request.GET.get('project', '')
    if project_id:
        prices = prices.filter(project_id=project_id)
    
    # Filter by material
    material_id = request.GET.get('material', '')
    if material_id:
        prices = prices.filter(material_id=material_id)
    
    # Filter by date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        prices = prices.filter(date__gte=date_from)
    if date_to:
        prices = prices.filter(date__lte=date_to)
    
    # Pagination
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    start = (page - 1) * page_size
    end = start + page_size
    
    total_count = prices.count()
    prices = prices.order_by('-date')[start:end]
    
    data = []
    for p in prices:
        variance = p.price_difference_from_standard()
        variance_percentage = p.price_difference_percentage()
        
        data.append({
            'id': p.id,
            'material_name': p.material.name,
            'material_id': p.material.id,
            'supplier_type': p.supplier_type,
            'supplier_type_display': p.get_supplier_type_display(),
            'supplier_name': p.supplier_name,
            'price': float(p.price),
            'date': p.date.isoformat(),
            'project_name': p.project.project_name if p.project else None,
            'project_id': p.project.id if p.project else None,
            'variance': float(variance),
            'variance_percentage': float(variance_percentage),
            'is_active': p.is_active,
            'notes': p.notes or ''
        })
    
    # Calculate comparison stats (using all data, not just paginated)
    all_prices = MaterialPriceMonitoring.objects.all()
    if supplier_type:
        all_prices = all_prices.filter(supplier_type=supplier_type)
    if project_id:
        all_prices = all_prices.filter(project_id=project_id)
    if material_id:
        all_prices = all_prices.filter(material_id=material_id)
    if date_from:
        all_prices = all_prices.filter(date__gte=date_from)
    if date_to:
        all_prices = all_prices.filter(date__lte=date_to)
    
    # Calculate averages for comparison
    regular_prices = all_prices.filter(supplier_type='REG')
    random_prices = all_prices.filter(supplier_type='RND')
    boq_prices = all_prices.filter(supplier_type='BOQ')
    quotation_prices = all_prices.filter(supplier_type='QUO')
    
    # Calculate averages with proper null handling
    def safe_avg(queryset):
        result = queryset.aggregate(avg=Avg('price'))
        return float(result['avg']) if result['avg'] is not None else 0.0
    
    comparison = {
        'avg_regular': safe_avg(regular_prices),
        'avg_random': safe_avg(random_prices),
        'avg_boq': safe_avg(boq_prices),
        'avg_quotation': safe_avg(quotation_prices)
    }
    
    # Debug logging
    print(f"DEBUG: Price monitoring comparison data: {comparison}")
    print(f"DEBUG: Regular prices count: {regular_prices.count()}")
    print(f"DEBUG: Random prices count: {random_prices.count()}")
    print(f"DEBUG: BOQ prices count: {boq_prices.count()}")
    print(f"DEBUG: Quotation prices count: {quotation_prices.count()}")
    
    return JsonResponse({
        'prices': data, 
        'count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size,
        'comparison': comparison
    })


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
