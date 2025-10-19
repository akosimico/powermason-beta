"""
Cost Learning Engine
Handles learning from actual project BOQ data to build cost intelligence
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from django.db import models
from django.utils import timezone
from django.db.models import Avg, Count, Q
from .models import ProjectType, ProjectTypeCostHistory, ProjectProfile


class CostLearningEngine:
    """
    Engine for learning cost patterns from actual project data
    """
    
    # Location multipliers (to be updated based on company data)
    LOCATION_MULTIPLIERS = {
        'NCR': Decimal('1.0'),              # Use company's actual ratio
        'CALABARZON': Decimal('1.0'),       # Update based on real regional differences
        'Central Luzon': Decimal('1.0'),    # Placeholder - replace with actual data
        'Cebu': Decimal('1.0'),
        'Davao': Decimal('1.0'),
        'default': Decimal('1.0'),
    }
    
    # Complexity multipliers (to be updated based on company data)
    COMPLEXITY_MULTIPLIERS = {
        'PUB': Decimal('1.0'),    # Update based on actual public vs private cost differences
        'PRI': Decimal('1.0'),    # Placeholder - replace with company data
        'REN': Decimal('1.0'),    # Compare renovation vs new build costs
        'NEW': Decimal('1.0'),    # Use actual company project data
    }
    
    @staticmethod
    def calculate_project_type_costs(project_type: ProjectType) -> Dict[str, Decimal]:
        """
        Calculate average costs from all approved history records
        """
        # Get all approved cost history for this project type
        history_records = ProjectTypeCostHistory.objects.filter(
            project_type=project_type,
            is_approved=True
        ).order_by('-uploaded_at')
        
        if not history_records.exists():
            return {}
        
        # Calculate weighted averages (recent projects weighted higher)
        total_weight = Decimal('0')
        weighted_costs = {
            'low_end': Decimal('0'),
            'mid_range': Decimal('0'),
            'high_end': Decimal('0'),
        }
        
        # Calculate weights based on recency (more recent = higher weight)
        for i, record in enumerate(history_records):
            # Weight decreases with age (most recent = weight 1.0, older = less)
            weight = Decimal('1.0') - (Decimal(str(i)) * Decimal('0.1'))
            weight = max(weight, Decimal('0.1'))  # Minimum weight of 0.1
            
            total_weight += weight
            
            # Add to complexity level averages
            complexity = record.complexity_level
            if complexity in weighted_costs:
                weighted_costs[complexity] += record.cost_per_sqm * weight
        
        # Calculate final averages
        if total_weight > 0:
            for complexity in weighted_costs:
                weighted_costs[complexity] = weighted_costs[complexity] / total_weight
        
        # Update ProjectType fields
        project_type.base_cost_low_end = weighted_costs.get('low_end')
        project_type.base_cost_mid_range = weighted_costs.get('mid_range')
        project_type.base_cost_high_end = weighted_costs.get('high_end')
        project_type.total_projects_count = history_records.count()
        project_type.last_cost_update = timezone.now()
        project_type.save()
        
        return weighted_costs
    
    @staticmethod
    def get_cost_estimate(
        project_type: ProjectType, 
        lot_size: Decimal, 
        location: str = None, 
        complexity: str = 'mid_range',
        project_category: str = None
    ) -> Dict:
        """
        Get cost estimate for new project based on learned data
        """
        # Check if project type has learned costs
        if not project_type.has_learned_costs():
            return {
                'success': False,
                'error': 'Insufficient cost data. Upload BOQ documents to build cost database.',
                'confidence': 'No Data',
                'sample_size': 0
            }
        
        # Get base cost for complexity level
        base_cost = project_type.get_base_cost(complexity)
        if not base_cost:
            return {
                'success': False,
                'error': f'No cost data available for {complexity} complexity level.',
                'confidence': 'No Data',
                'sample_size': 0
            }
        
        # Apply location multiplier
        location_multiplier = CostLearningEngine._get_location_multiplier(location)
        
        # Apply complexity multiplier
        complexity_multiplier = CostLearningEngine._get_complexity_multiplier(project_category)
        
        # Calculate adjusted cost per sqm
        adjusted_cost_per_sqm = base_cost * location_multiplier * complexity_multiplier
        
        # Calculate total cost
        total_cost = adjusted_cost_per_sqm * lot_size
        
        # Get cost breakdown
        breakdown = project_type.get_cost_breakdown()
        cost_breakdown = {}
        for category, percentage in breakdown.items():
            cost_breakdown[category] = total_cost * Decimal(str(percentage))
        
        # Calculate confidence level
        confidence = project_type.get_confidence_level()
        
        return {
            'success': True,
            'total_estimated_cost': total_cost,
            'cost_per_sqm': adjusted_cost_per_sqm,
            'base_cost_per_sqm': base_cost,
            'breakdown': cost_breakdown,
            'confidence': confidence,
            'sample_size': project_type.total_projects_count,
            'multipliers': {
                'location': location_multiplier,
                'complexity': complexity_multiplier,
            }
        }
    
    @staticmethod
    def add_boq_data_to_learning(
        project_type: ProjectType, 
        boq_data: Dict, 
        source: str = 'boq_upload',
        project: ProjectProfile = None,
        role: str = 'general_contractor'
    ) -> ProjectTypeCostHistory:
        """
        Add BOQ data to cost history with role support
        """
        # Create ProjectTypeCostHistory record
        cost_history = ProjectTypeCostHistory.objects.create(
            project_type=project_type,
            project=project,
            lot_size=boq_data.get('lot_size', Decimal('0')),
            total_cost=boq_data.get('total_cost', Decimal('0')),
            materials_cost=boq_data.get('materials_cost', Decimal('0')),
            labor_cost=boq_data.get('labor_cost', Decimal('0')),
            equipment_cost=boq_data.get('equipment_cost', Decimal('0')),
            permits_cost=boq_data.get('permits_cost', Decimal('0')),
            contingency_cost=boq_data.get('contingency_cost', Decimal('0')),
            overhead_cost=boq_data.get('overhead_cost', Decimal('0')),
            location=boq_data.get('location', ''),
            project_category=boq_data.get('project_category', ''),
            complexity_level=boq_data.get('complexity_level', 'mid_range'),
            project_role=role,
            source=source,
            is_approved=source == 'boq_upload',  # Auto-approve BOQ uploads
            approved_at=timezone.now() if source == 'boq_upload' else None
        )
        
        # Recalculate ProjectType average costs
        CostLearningEngine.calculate_project_type_costs(project_type)
        
        return cost_history
    
    @staticmethod
    def approve_project_costs(project: ProjectProfile) -> bool:
        """
        When project approved, add to learning database
        """
        if not project.extracted_total_cost or project.cost_data_contributed:
            return False
        
        # Get project's cost data
        boq_data = {
            'lot_size': project.lot_size or Decimal('0'),
            'total_cost': project.extracted_total_cost,
            'location': project.city_province or project.location,
            'project_category': project.project_category or 'PRI',
            'complexity_level': 'mid_range',  # Default, could be determined from other factors
        }
        
        # Add cost breakdown if available
        if project.extracted_cost_breakdown:
            breakdown = project.extracted_cost_breakdown
            boq_data.update({
                'materials_cost': breakdown.get('materials', Decimal('0')),
                'labor_cost': breakdown.get('labor', Decimal('0')),
                'equipment_cost': breakdown.get('equipment', Decimal('0')),
                'permits_cost': breakdown.get('permits', Decimal('0')),
                'contingency_cost': breakdown.get('contingency', Decimal('0')),
                'overhead_cost': breakdown.get('overhead', Decimal('0')),
            })
        
        # Determine role from project data
        role = 'general_contractor'  # Default
        if hasattr(project, 'project_role') and project.project_role:
            role = project.project_role.lower().replace(' ', '_')
        
        # Create cost history record
        cost_history = CostLearningEngine.add_boq_data_to_learning(
            project_type=project.project_type,
            boq_data=boq_data,
            source='project_completion',
            project=project,
            role=role
        )
        
        # Mark project as contributed
        project.cost_data_contributed = True
        project.save(update_fields=['cost_data_contributed'])
        
        return True
    
    @staticmethod
    def get_similar_projects(
        project_type: ProjectType, 
        lot_size: Decimal, 
        location: str = None
    ) -> List[ProjectTypeCostHistory]:
        """
        Find similar projects for better cost estimation
        """
        # Base query
        query = Q(project_type=project_type, is_approved=True)
        
        # Add location filter if provided
        if location:
            query &= Q(location__icontains=location)
        
        # Get projects with similar lot sizes (±20%)
        size_tolerance = lot_size * Decimal('0.2')
        min_size = lot_size - size_tolerance
        max_size = lot_size + size_tolerance
        
        query &= Q(lot_size__gte=min_size, lot_size__lte=max_size)
        
        return ProjectTypeCostHistory.objects.filter(query).order_by('-uploaded_at')[:10]
    
    @staticmethod
    def get_cost_statistics(project_type: ProjectType) -> Dict:
        """
        Get cost statistics for analytics
        """
        history_records = ProjectTypeCostHistory.objects.filter(
            project_type=project_type,
            is_approved=True
        )
        
        if not history_records.exists():
            return {
                'total_projects': 0,
                'average_cost_per_sqm': 0,
                'min_cost_per_sqm': 0,
                'max_cost_per_sqm': 0,
                'total_cost_range': (0, 0),
                'confidence_level': 'No Data'
            }
        
        costs_per_sqm = [record.cost_per_sqm for record in history_records]
        total_costs = [record.total_cost for record in history_records]
        
        return {
            'total_projects': history_records.count(),
            'average_cost_per_sqm': sum(costs_per_sqm) / len(costs_per_sqm),
            'min_cost_per_sqm': min(costs_per_sqm),
            'max_cost_per_sqm': max(costs_per_sqm),
            'total_cost_range': (min(total_costs), max(total_costs)),
            'confidence_level': project_type.get_confidence_level(),
            'last_update': project_type.last_cost_update
        }
    
    @staticmethod
    def _get_location_multiplier(location: str) -> Decimal:
        """Get location-based cost multiplier"""
        if not location:
            return Decimal('1.0')
        
        location_upper = location.upper()
        
        # Check for specific regions
        if any(region in location_upper for region in ['MANILA', 'QUEZON CITY', 'MAKATI', 'TAGUIG', 'PASAY']):
            return CostLearningEngine.LOCATION_MULTIPLIERS['NCR']
        elif any(region in location_upper for region in ['CAVITE', 'LAGUNA', 'BATANGAS', 'RIZAL']):
            return CostLearningEngine.LOCATION_MULTIPLIERS['CALABARZON']
        elif any(region in location_upper for region in ['BULACAN', 'PAMPANGA', 'NUEVA ECIJA']):
            return CostLearningEngine.LOCATION_MULTIPLIERS['Central Luzon']
        elif 'CEBU' in location_upper:
            return CostLearningEngine.LOCATION_MULTIPLIERS['Cebu']
        elif 'DAVAO' in location_upper:
            return CostLearningEngine.LOCATION_MULTIPLIERS['Davao']
        
        return CostLearningEngine.LOCATION_MULTIPLIERS['default']
    
    @staticmethod
    def _get_complexity_multiplier(project_category: str) -> Decimal:
        """Get project category-based complexity multiplier"""
        if not project_category:
            return Decimal('1.0')
        
        return CostLearningEngine.COMPLEXITY_MULTIPLIERS.get(project_category, Decimal('1.0'))
