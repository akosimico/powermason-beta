"""
Views for file preview and data extraction functionality
"""

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import os
import tempfile

from authentication.utils.decorators import verified_email_required, role_required
from .file_processing import FileProcessor, extract_cost_summary
from .boq_template import (
    create_hierarchical_boq_template,
    create_electrical_boq_template,
    create_mechanical_boq_template,
    create_civil_boq_template,
    create_architectural_boq_template
)
from .cost_learning import CostLearningEngine


@method_decorator([login_required, verified_email_required, role_required('EG', 'OM', 'PM')], name='dispatch')
class FilePreviewAPIView(View):
    """
    API endpoint for file preview and data extraction
    """
    
    def post(self, request):
        """Process uploaded file and return preview data"""
        try:
            # Check if file was uploaded
            if 'file' not in request.FILES:
                return JsonResponse({
                    'success': False,
                    'error': 'No file uploaded'
                }, status=400)
            
            uploaded_file = request.FILES['file']
            
            # Create file processor
            processor = FileProcessor(uploaded_file)
            
            # Extract and map data
            result = ProjectDataExtractor.extract_and_map_data(processor)
            
            if not result['success']:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Failed to process file')
                }, status=400)
            
            # Convert any non-serializable objects to strings
            def make_serializable(obj):
                if hasattr(obj, 'isoformat'):  # datetime objects
                    return obj.isoformat()
                elif hasattr(obj, '__dict__'):  # custom objects
                    return str(obj)
                return obj
            
            def clean_data(data):
                if isinstance(data, dict):
                    return {k: clean_data(v) for k, v in data.items()}
                elif isinstance(data, list):
                    return [clean_data(item) for item in data]
                else:
                    return make_serializable(data)
            
            cleaned_data = clean_data(result['data'])
            
            return JsonResponse({
                'success': True,
                'data': cleaned_data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error processing file: {str(e)}'
            }, status=500)


@login_required
@verified_email_required
@role_required('EG', 'OM', 'PM')
@require_http_methods(["POST"])
def file_preview_api(request):
    """
    Legacy API endpoint for file preview
    """
    try:
        # Check if file was uploaded
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No file uploaded'
            }, status=400)
        
        uploaded_file = request.FILES['file']
        
        # Create file processor
        processor = FileProcessor(uploaded_file)
        
        # Extract and map data
        result = ProjectDataExtractor.extract_and_map_data(processor)
        
        if not result['success']:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Failed to process file')
            }, status=400)
        
        # Convert any non-serializable objects to strings
        def make_serializable(obj):
            if hasattr(obj, 'isoformat'):  # datetime objects
                return obj.isoformat()
            elif hasattr(obj, '__dict__'):  # custom objects
                return str(obj)
            return obj
        
        def clean_data(data):
            if isinstance(data, dict):
                return {k: clean_data(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [clean_data(item) for item in data]
            else:
                return make_serializable(data)
        
        cleaned_data = clean_data(result['data'])
        
        return JsonResponse({
            'success': True,
            'data': cleaned_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error processing file: {str(e)}'
        }, status=500)


@login_required
@verified_email_required
@role_required('EG', 'OM', 'PM')
@require_http_methods(["POST"])
def save_extracted_data_api(request):
    """
    Save extracted data to project models
    """
    try:
        data = json.loads(request.body)
        
        # Get project ID
        project_id = data.get('project_id')
        if not project_id:
            return JsonResponse({
                'success': False,
                'error': 'Project ID is required'
            }, status=400)
        
        # Get extracted data
        extracted_data = data.get('extracted_data', {})
        mapped_models = extracted_data.get('mapped_models', {})
        
        # Import models here to avoid circular imports
        from .models import ProjectProfile
        from scheduling.models import ProjectTask, ProjectScope
        from materials_equipment.models import Material, Equipment
        
        try:
            project = ProjectProfile.objects.get(id=project_id)
        except ProjectProfile.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Project not found'
            }, status=404)
        
        saved_items = {
            'tasks': [],
            'materials': [],
            'equipment': [],
            'errors': []
        }
        
        # Save tasks
        tasks_data = mapped_models.get('tasks', [])
        if tasks_data:
            # Create a default scope if none exists
            default_scope, created = ProjectScope.objects.get_or_create(
                project=project,
                name='General Work',
                defaults={'weight': 100}
            )
            
            for task_data in tasks_data:
                try:
                    task = ProjectTask.objects.create(
                        project=project,
                        scope=default_scope,
                        task_name=task_data.get('task_name', 'Imported Task'),
                        description=task_data.get('description', ''),
                        start_date=project.start_date or project.created_at.date(),
                        end_date=project.target_completion_date or project.created_at.date(),
                        weight=task_data.get('suggested_weight', 10),
                        status=task_data.get('status', 'PL')
                    )
                    saved_items['tasks'].append({
                        'id': task.id,
                        'name': task.task_name
                    })
                except Exception as e:
                    saved_items['errors'].append(f"Failed to save task '{task_data.get('task_name', '')}': {str(e)}")
        
        # Save materials
        materials_data = mapped_models.get('materials', [])
        for material_data in materials_data:
            try:
                material = Material.objects.create(
                    name=material_data.get('name', 'Imported Material'),
                    description=material_data.get('notes', ''),
                    unit=material_data.get('unit', 'pcs'),
                    unit_cost=0,  # Default cost
                    supplier='Imported',
                    category='General'
                )
                saved_items['materials'].append({
                    'id': material.id,
                    'name': material.name
                })
            except Exception as e:
                saved_items['errors'].append(f"Failed to save material '{material_data.get('name', '')}': {str(e)}")
        
        # Save equipment
        equipment_data = mapped_models.get('equipment', [])
        for equipment_item in equipment_data:
            try:
                equipment = Equipment.objects.create(
                    name=equipment_item.get('name', 'Imported Equipment'),
                    description=equipment_item.get('notes', ''),
                    category='General',
                    status='available'
                )
                saved_items['equipment'].append({
                    'id': equipment.id,
                    'name': equipment.name
                })
            except Exception as e:
                saved_items['errors'].append(f"Failed to save equipment '{equipment_item.get('name', '')}': {str(e)}")
        
        return JsonResponse({
            'success': True,
            'saved_items': saved_items,
            'message': f"Successfully imported {len(saved_items['tasks'])} tasks, {len(saved_items['materials'])} materials, and {len(saved_items['equipment'])} equipment items."
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error saving data: {str(e)}'
        }, status=500)


@login_required
@verified_email_required
@role_required('EG', 'OM', 'PM')
@require_http_methods(["GET"])
def check_project_type_cost_data(request, project_type_id):
    """Check if project type has cost data and return estimates"""
    try:
        from .models import ProjectType, ProjectTypeCostHistory
        from django.db.models import Avg, Min, Max, Count
        
        # Get project type
        try:
            project_type = ProjectType.objects.get(id=project_type_id, is_active=True)
        except ProjectType.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Project type not found'
            }, status=404)
        
        # Query cost history for this project type
        cost_history = ProjectTypeCostHistory.objects.filter(
            project_type=project_type,
            is_approved=True
        )
        
        if not cost_history.exists():
            return JsonResponse({
                'success': True,
                'has_data': False,
                'message': 'No cost data available for this project type'
            })
        
        # Calculate statistics
        stats = cost_history.aggregate(
            avg_cost_per_sqm=Avg('cost_per_sqm'),
            min_total_cost=Min('total_cost'),
            max_total_cost=Max('total_cost'),
            avg_materials_cost=Avg('materials_cost'),
            avg_labor_cost=Avg('labor_cost'),
            avg_equipment_cost=Avg('equipment_cost'),
            sample_count=Count('id')
        )
        
        # Determine confidence level based on sample size
        sample_count = stats['sample_count']
        if sample_count >= 10:
            confidence_level = 'High'
        elif sample_count >= 5:
            confidence_level = 'Medium'
        else:
            confidence_level = 'Low'
        
        return JsonResponse({
            'success': True,
            'has_data': True,
            'cost_data': {
                'avg_cost_per_sqm': float(stats['avg_cost_per_sqm'] or 0),
                'min_total_cost': float(stats['min_total_cost'] or 0),
                'max_total_cost': float(stats['max_total_cost'] or 0),
                'avg_materials_cost': float(stats['avg_materials_cost'] or 0),
                'avg_labor_cost': float(stats['avg_labor_cost'] or 0),
                'avg_equipment_cost': float(stats['avg_equipment_cost'] or 0),
                'sample_count': sample_count,
                'confidence_level': confidence_level,
                'project_type_name': project_type.name
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error checking cost data: {str(e)}'
        }, status=500)


@login_required
@verified_email_required
@role_required('EG', 'OM', 'PM')
@require_http_methods(["GET"])
def get_project_type_boq_breakdown(request, project_type_id):
    """Get BOQ breakdown for a project type from recent projects"""
    try:
        from .models import ProjectType, ProjectProfile
        from django.db.models import Avg, Count
        
        # Get project type
        try:
            project_type = ProjectType.objects.get(id=project_type_id, is_active=True)
        except ProjectType.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Project type not found'
            }, status=404)
        
        # Get recent projects with BOQ data for this project type
        recent_projects = ProjectProfile.objects.filter(
            project_type=project_type,
            boq_items__isnull=False,
            boq_file_processed=True
        ).order_by('-created_at')[:5]  # Get 5 most recent projects
        
        if not recent_projects.exists():
            return JsonResponse({
                'success': True,
                'has_boq_data': False,
                'message': 'No BOQ data available for this project type'
            })
        
        # Aggregate BOQ data from recent projects
        all_boq_items = []
        for project in recent_projects:
            if project.boq_items:
                all_boq_items.extend(project.boq_items)
        
        if not all_boq_items:
            return JsonResponse({
                'success': True,
                'has_boq_data': False,
                'message': 'No BOQ items found in recent projects'
            })
        
        # Group BOQ items by category/section
        categories = {}
        for item in all_boq_items:
            category = item.get('section_category', 'General')
            if category not in categories:
                categories[category] = {
                    'items': [],
                    'total_cost': 0,
                    'item_count': 0
                }
            
            categories[category]['items'].append(item)
            categories[category]['total_cost'] += float(item.get('total_cost', 0))
            categories[category]['item_count'] += 1
        
        # Calculate average costs per category
        for category, data in categories.items():
            data['avg_cost'] = data['total_cost'] / len(recent_projects)
            data['avg_item_cost'] = data['total_cost'] / data['item_count'] if data['item_count'] > 0 else 0
        
        # Get most common items across all projects
        item_counts = {}
        for item in all_boq_items:
            description = item.get('description', '')
            if description:
                if description not in item_counts:
                    item_counts[description] = {
                        'count': 0,
                        'avg_cost': 0,
                        'total_cost': 0,
                        'category': item.get('section_category', 'General')
                    }
                item_counts[description]['count'] += 1
                item_counts[description]['total_cost'] += float(item.get('total_cost', 0))
        
        # Calculate averages for common items
        for description, data in item_counts.items():
            data['avg_cost'] = data['total_cost'] / data['count']
        
        # Get top 10 most common items
        common_items = sorted(item_counts.items(), key=lambda x: x[1]['count'], reverse=True)[:10]
        
        return JsonResponse({
            'success': True,
            'has_boq_data': True,
            'boq_breakdown': {
                'categories': categories,
                'common_items': [{'description': desc, **data} for desc, data in common_items],
                'total_projects_analyzed': len(recent_projects),
                'total_items_found': len(all_boq_items),
                'project_type_name': project_type.name
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error getting BOQ breakdown: {str(e)}'
        }, status=500)


@login_required
@verified_email_required
@role_required('EG', 'OM', 'PM')
@require_http_methods(["POST"])
def auto_configure_project_type_costs(request, project_type_id):
    """Automatically configure project type costs based on BOQ learning data"""
    try:
        from .models import ProjectType, ProjectTypeCostHistory
        from django.db.models import Avg, Count
        
        # Get project type
        try:
            project_type = ProjectType.objects.get(id=project_type_id, is_active=True)
        except ProjectType.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Project type not found'
            }, status=404)
        
        # Get cost history for this project type
        cost_history = ProjectTypeCostHistory.objects.filter(
            project_type=project_type,
            is_approved=True
        )
        
        if not cost_history.exists():
            return JsonResponse({
                'success': False,
                'error': 'No approved cost data available for this project type'
            })
        
        # Calculate average costs per complexity level
        low_end_data = cost_history.filter(complexity_level='low_end')
        mid_range_data = cost_history.filter(complexity_level='mid_range')
        high_end_data = cost_history.filter(complexity_level='high_end')
        
        # Update project type with learned costs
        if low_end_data.exists():
            project_type.base_cost_low_end = low_end_data.aggregate(avg=Avg('cost_per_sqm'))['avg']
        
        if mid_range_data.exists():
            project_type.base_cost_mid_range = mid_range_data.aggregate(avg=Avg('cost_per_sqm'))['avg']
        
        if high_end_data.exists():
            project_type.base_cost_high_end = high_end_data.aggregate(avg=Avg('cost_per_sqm'))['avg']
        
        # Calculate average cost breakdown percentages from all data
        all_data = cost_history.aggregate(
            avg_materials=Avg('materials_cost'),
            avg_labor=Avg('labor_cost'),
            avg_equipment=Avg('equipment_cost'),
            avg_permits=Avg('permits_cost'),
            avg_contingency=Avg('contingency_cost'),
            avg_overhead=Avg('overhead_cost'),
            avg_total=Avg('total_cost')
        )
        
        total_cost = all_data['avg_total'] or 1  # Avoid division by zero
        
        # Calculate percentages
        project_type.materials_percentage = (all_data['avg_materials'] / total_cost * 100) if total_cost else 40.00
        project_type.labor_percentage = (all_data['avg_labor'] / total_cost * 100) if total_cost else 30.00
        project_type.equipment_percentage = (all_data['avg_equipment'] / total_cost * 100) if total_cost else 10.00
        project_type.permits_percentage = (all_data['avg_permits'] / total_cost * 100) if total_cost else 5.00
        project_type.contingency_percentage = (all_data['avg_contingency'] / total_cost * 100) if total_cost else 10.00
        project_type.overhead_percentage = (all_data['avg_overhead'] / total_cost * 100) if total_cost else 5.00
        
        # Update learning tracking
        project_type.total_projects_count = cost_history.count()
        project_type.last_cost_update = timezone.now()
        
        project_type.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Cost configuration updated based on {cost_history.count()} approved projects',
            'cost_data': {
                'base_cost_low_end': float(project_type.base_cost_low_end) if project_type.base_cost_low_end else None,
                'base_cost_mid_range': float(project_type.base_cost_mid_range) if project_type.base_cost_mid_range else None,
                'base_cost_high_end': float(project_type.base_cost_high_end) if project_type.base_cost_high_end else None,
                'materials_percentage': float(project_type.materials_percentage),
                'labor_percentage': float(project_type.labor_percentage),
                'equipment_percentage': float(project_type.equipment_percentage),
                'permits_percentage': float(project_type.permits_percentage),
                'contingency_percentage': float(project_type.contingency_percentage),
                'overhead_percentage': float(project_type.overhead_percentage),
                'total_projects_count': project_type.total_projects_count
            }
        })
        
    except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error auto-configuring costs: {str(e)}'
            }, status=500)

@login_required
@verified_email_required
@role_required('EG', 'OM', 'PM')
@require_http_methods(["GET"])
def export_boq_to_excel(request, project_id):
    """Export BOQ data to Excel file"""
    try:
        from .models import ProjectProfile
        import pandas as pd
        from django.http import HttpResponse
        import io
        
        # Get project
        try:
            project = ProjectProfile.objects.get(id=project_id)
        except ProjectProfile.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Project not found'
            }, status=404)
        
        if not project.boq_items:
            return JsonResponse({
                'success': False,
                'error': 'No BOQ data available for this project'
            }, status=400)
        
        # Create Excel file
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Project Information Sheet
            project_info = {
                'Project Name': [project.project_name],
                'Project ID': [project.project_id],
                'Project Type': [project.project_type.name if project.project_type else ''],
                'Client': [project.client.company_name if project.client else ''],
                'Location': [project.location or ''],
                'Lot Size (sqm)': [float(project.lot_size) if project.lot_size else 0],
                'Total Cost': [float(project.extracted_total_cost) if project.extracted_total_cost else 0],
                'Cost per sqm': [float(project.extracted_total_cost / project.lot_size) if project.lot_size and project.extracted_total_cost else 0],
                'Project Role': [project.project_role or 'General Contractor'],
                'Date Created': [project.created_at.strftime('%Y-%m-%d')],
                'Status': [project.get_status_display()]
            }
            
            project_df = pd.DataFrame(project_info)
            project_df.to_excel(writer, sheet_name='Project Info', index=False)
            
            # BOQ Items Sheet
            boq_data = []
            for item in project.boq_items:
                boq_data.append({
                    'Item #': item.get('item_number', ''),
                    'Description': item.get('description', ''),
                    'Section/Category': item.get('section', ''),
                    'UOM': item.get('uom', ''),
                    'Quantity': float(item.get('quantity', 0)),
                    'Unit Cost': float(item.get('unit_cost', 0)),
                    'Total Cost': float(item.get('total_cost', 0)),
                    'Material Cost': float(item.get('material_cost', 0)),
                    'Labor Cost': float(item.get('labor_cost', 0)),
                    'Equipment Cost': float(item.get('equipment_cost', 0)),
                    'Subcontractor Cost': float(item.get('subcontractor_cost', 0)),
                    'Dependencies': ', '.join(item.get('dependencies', [])) if item.get('dependencies') else '',
                    'Remarks': item.get('remarks', '')
                })
            
            boq_df = pd.DataFrame(boq_data)
            boq_df.to_excel(writer, sheet_name='BOQ Items', index=False)
            
            # Cost Summary Sheet
            if project.extracted_cost_breakdown:
                cost_summary = []
                for category, amount in project.extracted_cost_breakdown.items():
                    cost_summary.append({
                        'Category': category.title(),
                        'Amount': float(amount),
                        'Percentage': float(amount / project.extracted_total_cost * 100) if project.extracted_total_cost else 0
                    })
                
                cost_df = pd.DataFrame(cost_summary)
                cost_df.to_excel(writer, sheet_name='Cost Summary', index=False)
        
        output.seek(0)
        
        # Create response
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="BOQ_{project.project_id}_{project.project_name.replace(" ", "_")}.xlsx"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting BOQ to Excel: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error exporting BOQ: {str(e)}'
        }, status=500)


@login_required
@verified_email_required
@role_required('EG', 'OM', 'PM')
@require_http_methods(["GET"])
def download_boq_template(request):
    try:
        content = create_hierarchical_boq_template()
        response = HttpResponse(content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="BOQ_Hierarchical_Template.xlsx"'
        return response
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@verified_email_required
@role_required('EG', 'OM', 'PM')
@require_http_methods(["GET"])
def download_electrical_boq_template(request):
    try:
        content = create_electrical_boq_template()
        response = HttpResponse(content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="Electrical_BOQ_Template.xlsx"'
        return response
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@verified_email_required
@role_required('EG', 'OM', 'PM')
@require_http_methods(["GET"])
def download_mechanical_boq_template(request):
    try:
        content = create_mechanical_boq_template()
        response = HttpResponse(content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="Mechanical_BOQ_Template.xlsx"'
        return response
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@verified_email_required
@role_required('EG', 'OM', 'PM')
@require_http_methods(["GET"])
def download_civil_boq_template(request):
    try:
        content = create_civil_boq_template()
        response = HttpResponse(content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="Civil_BOQ_Template.xlsx"'
        return response
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@verified_email_required
@role_required('EG', 'OM', 'PM')
@require_http_methods(["GET"])
def download_architectural_boq_template(request):
    try:
        content = create_architectural_boq_template()
        response = HttpResponse(content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="Architectural_BOQ_Template.xlsx"'
        return response
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@method_decorator([login_required, verified_email_required, role_required('EG', 'OM')], name='dispatch')
class BOQUploadAPIView(View):
    """
    API endpoint for uploading BOQ files to project types
    """
    
    def post(self, request):
        """Upload and process BOQ file for cost learning"""
        try:
            # Get uploaded file
            file = request.FILES.get('file')
            if not file:
                return JsonResponse({
                    'success': False,
                    'error': 'No file uploaded'
                }, status=400)
            
            # Preview-only mode (force no saving even if project_type provided)
            preview_only = request.POST.get('preview') in ['1', 'true', 'True']

            # Get project type ID (optional)
            project_type_id = request.POST.get('project_type_id')
            project_type = None
            if project_type_id:
                try:
                    from .models import ProjectType
                    project_type = ProjectType.objects.get(id=project_type_id, is_active=True)
                except ProjectType.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid project type ID'
                    }, status=400)
            
            # Validate file
            processor = FileProcessor(file)
            if not processor.is_supported():
                return JsonResponse({
                    'success': False,
                    'error': 'Unsupported file type. Please upload PDF or Excel files.'
                }, status=400)
            
            if not processor.is_valid_size():
                return JsonResponse({
                    'success': False,
                    'error': 'File too large. Maximum size is 10MB.'
                }, status=400)
            
            # Read file content
            file_content = file.read()
            file_extension = os.path.splitext(file.name)[1].lower()
            
            # Extract cost data
            cost_data = extract_cost_summary(file_content, file_extension)
            
            # Debug logging
            print(f"DEBUG: BOQ file processing - File: {file.name}, Extension: {file_extension}")
            print(f"DEBUG: Extraction result - Success: {cost_data.get('success')}, Items: {len(cost_data.get('boq_items', []))}")
            
            if not cost_data.get('success'):
                return JsonResponse({
                    'success': False,
                    'error': cost_data.get('error', 'Failed to extract cost data')
                }, status=400)
            
            # If project type is specified, add to learning database (unless preview-only)
            if project_type and not preview_only:
                try:
                    # Add BOQ data to cost learning
                    cost_history = CostLearningEngine.add_boq_data_to_learning(
                        project_type=project_type,
                        boq_data=cost_data,
                        source='boq_upload',
                        role=cost_data.get('role', 'general_contractor')
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'BOQ file processed successfully. Cost data added to {project_type.name} learning database.',
                        'cost_data': {
                            'total_cost': str(cost_data.get('total_cost', 0)),
                            'lot_size': str(cost_data.get('lot_size', 0)),
                            'cost_per_sqm': str(cost_data.get('cost_per_sqm', 0)),
                            'project_type': project_type.name
                        }
                    })
                    
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': f'Error adding to learning database: {str(e)}'
                    }, status=500)
            else:
                # Return extracted data without adding to learning database
                return JsonResponse({
                    'success': True,
                    'message': 'BOQ file processed successfully. Cost data extracted (preview-only).',
                    'cost_data': {
                        'total_cost': str(cost_data.get('total_cost', 0)),
                        'lot_size': str(cost_data.get('lot_size', 0)),
                        'cost_per_sqm': str(cost_data.get('cost_per_sqm', 0)),
                        'materials_cost': str(cost_data.get('materials_cost', 0)),
                        'labor_cost': str(cost_data.get('labor_cost', 0)),
                        'equipment_cost': str(cost_data.get('equipment_cost', 0)),
                        'permits_cost': str(cost_data.get('permits_cost', 0)),
                        'contingency_cost': str(cost_data.get('contingency_cost', 0)),
                        'overhead_cost': str(cost_data.get('overhead_cost', 0)),
                        'boq_items': cost_data.get('boq_items', []),
                        'project_info': cost_data.get('project_info', {}),
                        'extracted_cost_breakdown': {
                            'materials': str(cost_data.get('materials_cost', 0)),
                            'labor': str(cost_data.get('labor_cost', 0)),
                            'equipment': str(cost_data.get('equipment_cost', 0)),
                            'subcontractor': str(cost_data.get('subcontractor_cost', 0)),
                            'permits': str(cost_data.get('permits_cost', 0)),
                            'contingency': str(cost_data.get('contingency_cost', 0)),
                            'overhead': str(cost_data.get('overhead_cost', 0)),
                        }
                    }
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error processing BOQ file: {str(e)}'
            }, status=500)


@login_required
@verified_email_required
@role_required('EG', 'OM', 'PM')
@require_http_methods(["GET", "POST"])
def boq_preview_test(request):
    if request.method == "GET":
        return render(request, "project_profiling/boq_preview_test.html")
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'success': False, 'error': 'No file uploaded'}, status=400)
    try:
        file_content = file.read()
        ext = os.path.splitext(file.name)[1].lower()
        data = extract_cost_summary(file_content, ext)
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
