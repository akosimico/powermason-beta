"""
Automatic Cost Estimation System
Calculates project costs based on project type, lot size, and other factors
"""

from decimal import Decimal
from typing import Dict, List, Optional
from django.db import models
from .models import ProjectProfile, ProjectType
from .cost_configuration import (
    CostConfiguration, 
    SizeMultiplier, 
    LocationMultiplier, 
    ComplexityMultiplier,
    CostBreakdownTemplate
)


class CostEstimationEngine:
    """
    Engine for calculating automatic cost estimates based on project parameters
    """
    
    # Base cost per square meter for different project types (in PHP)
    BASE_COSTS_PER_SQM = {
        'residential': {
            'low_end': Decimal('15000'),      # Basic residential
            'mid_range': Decimal('25000'),    # Standard residential
            'high_end': Decimal('40000'),     # Luxury residential
        },
        'commercial': {
            'low_end': Decimal('20000'),      # Basic commercial
            'mid_range': Decimal('35000'),    # Standard commercial
            'high_end': Decimal('55000'),     # Premium commercial
        },
        'industrial': {
            'low_end': Decimal('12000'),      # Basic industrial
            'mid_range': Decimal('20000'),    # Standard industrial
            'high_end': Decimal('30000'),     # Advanced industrial
        },
        'infrastructure': {
            'low_end': Decimal('8000'),       # Basic infrastructure
            'mid_range': Decimal('15000'),    # Standard infrastructure
            'high_end': Decimal('25000'),     # Complex infrastructure
        },
        'renovation': {
            'low_end': Decimal('8000'),       # Basic renovation
            'mid_range': Decimal('15000'),    # Standard renovation
            'high_end': Decimal('25000'),     # Complete renovation
        }
    }
    
    # Complexity multipliers based on project category
    COMPLEXITY_MULTIPLIERS = {
        'PUB': Decimal('1.0'),    # Public - standard
        'PRI': Decimal('1.1'),    # Private - slightly higher
        'REN': Decimal('0.8'),    # Renovation - lower base cost
        'NEW': Decimal('1.2'),    # New build - higher complexity
    }
    
    # Size-based adjustments
    SIZE_MULTIPLIERS = {
        'small': {'min': 0, 'max': 100, 'multiplier': Decimal('1.3')},      # Small projects cost more per sqm
        'medium': {'min': 100, 'max': 500, 'multiplier': Decimal('1.0')},   # Standard
        'large': {'min': 500, 'max': 2000, 'multiplier': Decimal('0.9')},   # Large projects get discount
        'xlarge': {'min': 2000, 'max': float('inf'), 'multiplier': Decimal('0.8')},  # Very large projects
    }
    
    # Location-based adjustments (Philippines regions)
    LOCATION_MULTIPLIERS = {
        'NCR': Decimal('1.3'),        # Metro Manila - highest cost
        'CALABARZON': Decimal('1.2'), # Cavite, Laguna, Batangas, Rizal, Quezon
        'Central Luzon': Decimal('1.1'),
        'Cebu': Decimal('1.2'),       # Major cities
        'Davao': Decimal('1.1'),
        'default': Decimal('1.0'),    # Other regions
    }
    
    @classmethod
    def estimate_project_cost(
        cls,
        project_type: str,
        lot_size: Optional[Decimal],
        project_category: str,
        location: str = '',
        complexity_level: str = 'mid_range'
    ) -> Dict[str, Decimal]:
        """
        Calculate estimated project cost based on various factors
        
        Args:
            project_type: Type of project (residential, commercial, etc.)
            lot_size: Size of the lot in square meters
            project_category: Project category (PUB, PRI, REN, NEW)
            location: Project location for regional adjustments
            complexity_level: low_end, mid_range, or high_end
            
        Returns:
            Dictionary with cost breakdown
        """
        if not lot_size or lot_size <= 0:
            return {
                'base_cost': Decimal('0'),
                'total_estimated_cost': Decimal('0'),
                'cost_per_sqm': Decimal('0'),
                'breakdown': {}
            }
        
        # Get base cost per square meter
        base_cost_per_sqm = cls._get_base_cost_per_sqm(project_type, complexity_level)
        
        # Apply size multiplier
        size_multiplier = cls._get_size_multiplier(lot_size)
        
        # Apply complexity multiplier
        complexity_multiplier = cls.COMPLEXITY_MULTIPLIERS.get(project_category, Decimal('1.0'))
        
        # Apply location multiplier
        location_multiplier = cls._get_location_multiplier(location)
        
        # Calculate adjusted cost per square meter
        adjusted_cost_per_sqm = (
            base_cost_per_sqm * 
            size_multiplier * 
            complexity_multiplier * 
            location_multiplier
        )
        
        # Calculate base cost
        base_cost = lot_size * adjusted_cost_per_sqm
        
        # Calculate cost breakdown
        breakdown = cls._calculate_cost_breakdown(base_cost, project_type)
        
        return {
            'base_cost': base_cost,
            'total_estimated_cost': sum(breakdown.values()),
            'cost_per_sqm': adjusted_cost_per_sqm,
            'breakdown': breakdown,
            'multipliers': {
                'size': size_multiplier,
                'complexity': complexity_multiplier,
                'location': location_multiplier,
            }
        }
    
    @classmethod
    def _get_base_cost_per_sqm(cls, project_type: str, complexity_level: str) -> Decimal:
        """Get base cost per square meter for project type and complexity"""
        # If project_type is a ProjectType instance, use it directly
        if hasattr(project_type, 'get_base_cost'):
            base_cost = project_type.get_base_cost(complexity_level)
            if base_cost:
                return base_cost
        
        # If project_type is a string, try to find the ProjectType
        if isinstance(project_type, str):
            try:
                from .models import ProjectType
                project_type_obj = ProjectType.objects.get(name__iexact=project_type, is_active=True)
                base_cost = project_type_obj.get_base_cost(complexity_level)
                if base_cost:
                    return base_cost
            except ProjectType.DoesNotExist:
                pass
        
        # Fallback to hardcoded values
        normalized_type = project_type.lower().replace(' ', '_') if isinstance(project_type, str) else 'residential'
        
        type_mapping = {
            'house': 'residential',
            'residential': 'residential',
            'apartment': 'residential',
            'condo': 'residential',
            'office': 'commercial',
            'commercial': 'commercial',
            'retail': 'commercial',
            'warehouse': 'industrial',
            'industrial': 'industrial',
            'factory': 'industrial',
            'road': 'infrastructure',
            'bridge': 'infrastructure',
            'infrastructure': 'infrastructure',
            'renovation': 'renovation',
            'remodel': 'renovation',
        }
        
        mapped_type = type_mapping.get(normalized_type, 'residential')
        return cls.BASE_COSTS_PER_SQM.get(mapped_type, {}).get(complexity_level, Decimal('20000'))
    
    @classmethod
    def _get_size_multiplier(cls, lot_size: Decimal) -> Decimal:
        """Get size-based cost multiplier"""
        size_value = float(lot_size)
        
        # Try to get from database configuration first
        try:
            multipliers = SizeMultiplier.objects.filter(is_active=True).order_by('min_size')
            for multiplier in multipliers:
                if multiplier.max_size is None:
                    # No upper limit
                    if size_value >= float(multiplier.min_size):
                        return multiplier.multiplier
                else:
                    # Has upper limit
                    if float(multiplier.min_size) <= size_value < float(multiplier.max_size):
                        return multiplier.multiplier
        except Exception:
            pass
        
        # Fallback to hardcoded values
        for size_category, config in cls.SIZE_MULTIPLIERS.items():
            if config['min'] <= size_value < config['max']:
                return config['multiplier']
        
        return Decimal('1.0')
    
    @classmethod
    def _get_location_multiplier(cls, location: str) -> Decimal:
        """Get location-based cost multiplier"""
        location_upper = location.upper()
        
        # Try to get from database configuration first
        try:
            multipliers = LocationMultiplier.objects.filter(is_active=True).exclude(is_default=True)
            for multiplier in multipliers:
                keywords = multiplier.get_keywords_list()
                if any(keyword.upper() in location_upper for keyword in keywords):
                    return multiplier.multiplier
            
            # Check for default multiplier
            default_multiplier = LocationMultiplier.objects.filter(is_default=True, is_active=True).first()
            if default_multiplier:
                return default_multiplier.multiplier
        except Exception:
            pass
        
        # Fallback to hardcoded values
        if any(region in location_upper for region in ['MANILA', 'QUEZON CITY', 'MAKATI', 'TAGUIG', 'PASAY']):
            return cls.LOCATION_MULTIPLIERS['NCR']
        elif any(region in location_upper for region in ['CAVITE', 'LAGUNA', 'BATANGAS', 'RIZAL']):
            return cls.LOCATION_MULTIPLIERS['CALABARZON']
        elif any(region in location_upper for region in ['BULACAN', 'PAMPANGA', 'NUEVA ECIJA']):
            return cls.LOCATION_MULTIPLIERS['Central Luzon']
        elif 'CEBU' in location_upper:
            return cls.LOCATION_MULTIPLIERS['Cebu']
        elif 'DAVAO' in location_upper:
            return cls.LOCATION_MULTIPLIERS['Davao']
        
        return cls.LOCATION_MULTIPLIERS['default']
    
    @classmethod
    def _calculate_cost_breakdown(cls, base_cost: Decimal, project_type: str, complexity_level: str = 'mid_range') -> Dict[str, Decimal]:
        """Calculate detailed cost breakdown by category"""
        
        # If project_type is a ProjectType instance, use its breakdown
        if hasattr(project_type, 'get_cost_breakdown'):
            percentages = project_type.get_cost_breakdown()
        # If project_type is a string, try to find the ProjectType
        elif isinstance(project_type, str):
            try:
                from .models import ProjectType
                project_type_obj = ProjectType.objects.get(name__iexact=project_type, is_active=True)
                percentages = project_type_obj.get_cost_breakdown()
            except ProjectType.DoesNotExist:
                # Fallback to hardcoded values
                percentages = cls._get_fallback_breakdown(project_type)
        else:
            # Fallback to hardcoded values
            percentages = cls._get_fallback_breakdown(project_type)
        
        breakdown = {}
        for category, percentage in percentages.items():
            breakdown[category] = base_cost * Decimal(str(percentage))
        
        return breakdown
    
    @classmethod
    def _get_fallback_breakdown(cls, project_type: str) -> Dict[str, float]:
        """Get fallback breakdown percentages"""
        normalized_type = project_type.lower().replace(' ', '_') if isinstance(project_type, str) else 'residential'
        
        type_mapping = {
            'house': 'residential',
            'residential': 'residential',
            'apartment': 'residential',
            'condo': 'residential',
            'office': 'commercial',
            'commercial': 'commercial',
            'retail': 'commercial',
            'warehouse': 'industrial',
            'industrial': 'industrial',
            'factory': 'industrial',
            'road': 'infrastructure',
            'bridge': 'infrastructure',
            'infrastructure': 'infrastructure',
            'renovation': 'renovation',
            'remodel': 'renovation',
        }
        
        mapped_type = type_mapping.get(normalized_type, 'residential')
        
        breakdown_percentages = {
            'residential': {
                'materials': 0.40,
                'labor': 0.30,
                'equipment': 0.10,
                'permits': 0.05,
                'contingency': 0.10,
                'overhead': 0.05,
            },
            'commercial': {
                'materials': 0.35,
                'labor': 0.25,
                'equipment': 0.15,
                'permits': 0.08,
                'contingency': 0.12,
                'overhead': 0.05,
            },
            'industrial': {
                'materials': 0.30,
                'labor': 0.20,
                'equipment': 0.25,
                'permits': 0.10,
                'contingency': 0.10,
                'overhead': 0.05,
            },
            'infrastructure': {
                'materials': 0.45,
                'labor': 0.25,
                'equipment': 0.15,
                'permits': 0.05,
                'contingency': 0.05,
                'overhead': 0.05,
            },
            'renovation': {
                'materials': 0.50,
                'labor': 0.30,
                'equipment': 0.05,
                'permits': 0.05,
                'contingency': 0.05,
                'overhead': 0.05,
            }
        }
        
        return breakdown_percentages.get(mapped_type, breakdown_percentages['residential'])


class ProjectCostEstimator:
    """
    High-level interface for project cost estimation
    """
    
    @staticmethod
    def estimate_for_project(project: ProjectProfile) -> Dict[str, Decimal]:
        """
        Estimate costs for a specific project instance
        """
        if not project.lot_size:
            return {
                'base_cost': Decimal('0'),
                'total_estimated_cost': Decimal('0'),
                'cost_per_sqm': Decimal('0'),
                'breakdown': {},
                'message': 'Lot size required for cost estimation'
            }
        
        project_type_name = project.project_type.name if project.project_type else 'residential'
        project_category = project.project_category or 'PRI'
        location = project.city_province or project.location or ''
        
        return CostEstimationEngine.estimate_project_cost(
            project_type=project_type_name,
            lot_size=project.lot_size,
            project_category=project_category,
            location=location,
            complexity_level='mid_range'  # Default to mid-range
        )
    
    @staticmethod
    def get_estimation_options() -> Dict[str, List[str]]:
        """
        Get available options for cost estimation
        """
        return {
            'complexity_levels': ['low_end', 'mid_range', 'high_end'],
            'project_types': list(CostEstimationEngine.BASE_COSTS_PER_SQM.keys()),
            'project_categories': list(CostEstimationEngine.COMPLEXITY_MULTIPLIERS.keys()),
        }
