"""
Views for cost estimation functionality
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
import json
from decimal import Decimal

from authentication.utils.decorators import verified_email_required, role_required
from authentication.utils.tokens import get_user_profile, verify_user_profile
from .cost_estimation import CostEstimationEngine, ProjectCostEstimator
from .cost_learning import CostLearningEngine


@method_decorator([login_required, verified_email_required, role_required('EG', 'OM', 'PM')], name='dispatch')
class CostEstimationAPIView(View):
    """
    API endpoint for cost estimation
    """
    
    def post(self, request):
        """Calculate cost estimation based on provided parameters"""
        try:
            data = json.loads(request.body)
            
            # Extract parameters
            project_type = data.get('project_type', 'residential')
            lot_size = data.get('lot_size')
            project_category = data.get('project_category', 'PRI')
            location = data.get('location', '')
            complexity_level = data.get('complexity_level', 'mid_range')
            
            # Validate required fields
            if not lot_size:
                return JsonResponse({
                    'error': 'Lot size is required for cost estimation'
                }, status=400)
            
            # Convert lot_size to Decimal
            try:
                lot_size_decimal = Decimal(str(lot_size))
            except (ValueError, TypeError):
                return JsonResponse({
                    'error': 'Invalid lot size format'
                }, status=400)
            
            # Try to get ProjectType instance if project_type is an ID
            project_type_obj = None
            if str(project_type).isdigit():
                try:
                    from .models import ProjectType
                    project_type_obj = ProjectType.objects.get(id=project_type, is_active=True)
                except ProjectType.DoesNotExist:
                    pass
            
            # First try to use learned costs
            if project_type_obj:
                estimation = CostLearningEngine.get_cost_estimate(
                    project_type=project_type_obj,
                    lot_size=lot_size_decimal,
                    location=location,
                    complexity=complexity_level,
                    project_category=project_category
                )
                
                # If learned costs available, use them
                if estimation.get('success'):
                    # Convert Decimal values to strings for JSON serialization
                    def convert_decimals(obj):
                        if isinstance(obj, Decimal):
                            return str(obj)
                        elif isinstance(obj, dict):
                            return {k: convert_decimals(v) for k, v in obj.items()}
                        elif isinstance(obj, list):
                            return [convert_decimals(item) for item in obj]
                        return obj
                    
                    estimation = convert_decimals(estimation)
                    return JsonResponse({
                        'success': True,
                        'estimation': estimation,
                        'source': 'learned_data'
                    })
            
            # Fallback to traditional estimation if no learned data
            estimation = CostEstimationEngine.estimate_project_cost(
                project_type=project_type_obj or project_type,
                lot_size=lot_size_decimal,
                project_category=project_category,
                location=location,
                complexity_level=complexity_level
            )
            
            # Convert Decimal values to strings for JSON serialization
            def convert_decimals(obj):
                if isinstance(obj, Decimal):
                    return str(obj)
                elif isinstance(obj, dict):
                    return {k: convert_decimals(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_decimals(item) for item in obj]
                return obj
            
            estimation = convert_decimals(estimation)
            
            return JsonResponse({
                'success': True,
                'estimation': estimation,
                'source': 'fallback_estimation'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': f'Estimation failed: {str(e)}'
            }, status=500)
    
    def get(self, request):
        """Get available estimation options"""
        try:
            options = ProjectCostEstimator.get_estimation_options()
            return JsonResponse({
                'success': True,
                'options': options
            })
        except Exception as e:
            return JsonResponse({
                'error': f'Failed to get options: {str(e)}'
            }, status=500)


@login_required
@verified_email_required
@role_required('EG', 'OM', 'PM')
@require_http_methods(["POST"])
def estimate_project_cost_api(request):
    """
    API endpoint for cost estimation
    """
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return JsonResponse({"error": "Authentication required"}, status=403)
    
    try:
        data = json.loads(request.body)
        
        # Extract parameters
        project_type = data.get('project_type', 'residential')
        lot_size = data.get('lot_size')
        project_category = data.get('project_category', 'PRI')
        location = data.get('location', '')
        complexity_level = data.get('complexity_level', 'mid_range')
        
        # Validate required fields
        if not lot_size:
            return JsonResponse({
                'error': 'Lot size is required for cost estimation'
            }, status=400)
        
        # Convert lot_size to Decimal
        try:
            lot_size_decimal = Decimal(str(lot_size))
        except (ValueError, TypeError):
            return JsonResponse({
                'error': 'Invalid lot size format'
            }, status=400)
        
        # Calculate estimation
        estimation = CostEstimationEngine.estimate_project_cost(
            project_type=project_type,
            lot_size=lot_size_decimal,
            project_category=project_category,
            location=location,
            complexity_level=complexity_level
        )
        
        # Convert Decimal values to strings for JSON serialization
        def convert_decimals(obj):
            if isinstance(obj, Decimal):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            return obj
        
        estimation = convert_decimals(estimation)
        
        return JsonResponse({
            'success': True,
            'estimation': estimation
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Estimation failed: {str(e)}'
        }, status=500)


@login_required
@verified_email_required
@role_required('EG', 'OM', 'PM')
@require_http_methods(["GET"])
def get_estimation_options_api(request):
    """
    Get available estimation options
    """
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return JsonResponse({"error": "Authentication required"}, status=403)
    
    try:
        options = ProjectCostEstimator.get_estimation_options()
        return JsonResponse({
            'success': True,
            'options': options
        })
    except Exception as e:
        return JsonResponse({
            'error': f'Failed to get options: {str(e)}'
        }, status=500)
