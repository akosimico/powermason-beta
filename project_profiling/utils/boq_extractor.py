"""
BOQ Data Extraction and Entity Creation

This module handles the automatic extraction of BOQ data and creation of project entities
(scopes, tasks, materials, equipment, mobilization costs) when a project budget is approved.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Tuple, Any
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from project_profiling.models import ProjectProfile
from scheduling.models import ProjectScope, ProjectTask
from materials_equipment.models import Material, Equipment, GeneralRequirement, ProjectGeneralRequirement, ProjectMaterial, ProjectEquipment

logger = logging.getLogger(__name__)
User = get_user_model()

# Work type specific equipment/materials for your 4 work types
WORK_TYPE_CLASSIFICATIONS = {
    'electrical': {
        'equipment': ['generator', 'transformer', 'ats', 'testing equipment', 
                     'aircon unit', 'hvac unit', 'ups', 'inverter', 'panel',
                     'breaker', 'switch', 'outlet', 'cable', 'conduit'],
        'category': 'Electrical'
    },
    'civil': {
        'equipment': ['excavator', 'concrete mixer', 'vibrator', 'pump', 
                     'crane', 'compactor', 'roller', 'bulldozer', 'backhoe',
                     'loader', 'grader', 'paver'],
        'category': 'Civil'
    },
    'architectural': {
        'equipment': ['scaffolding', 'hoist', 'lift', 'crane', 'platform'],
        'category': 'Architectural'
    },
    'mechanical': {
        'equipment': ['pump', 'chiller', 'boiler', 'compressor', 'fan',
                     'aircon', 'water heater', 'water tank', 'motor',
                     'generator', 'compressor unit'],
        'category': 'Mechanical'
    }
}


def classify_boq_item(boq_item: Dict[str, Any], project_work_type: str = 'general') -> str:
    """
    Classify a BOQ item as mobilization, equipment, or material.
    
    Args:
        boq_item: BOQ item dictionary with description, is_requirement, etc.
        project_work_type: Type of work (electrical, civil, architectural, mechanical)
    
    Returns:
        str: 'mobilization', 'equipment', or 'material'
    """
    # Priority 1: Check is_requirement flag (already set by file_processing.py)
    if boq_item.get('is_requirement', False):
        return 'mobilization'
    
    # Priority 2: Work-type specific equipment keywords
    description = str(boq_item.get('description', '')).lower()
    if project_work_type in WORK_TYPE_CLASSIFICATIONS:
        keywords = WORK_TYPE_CLASSIFICATIONS[project_work_type]['equipment']
        if any(kw in description for kw in keywords):
            return 'equipment'
    
    # Default: Material
    return 'material'


def get_project_work_type(project: ProjectProfile) -> str:
    """
    Determine the work type from project data.
    
    Args:
        project: ProjectProfile instance
    
    Returns:
        str: Work type (electrical, civil, architectural, mechanical, general)
    """
    # For ProjectProfile, check project_type field directly
    work_type = getattr(project, 'project_type', '')
    if hasattr(project, 'project_type') and project.project_type:
        work_type = str(project.project_type).lower()
    else:
        work_type = 'general'
    
    # Map common terms to our classifications
    if any(term in work_type.lower() for term in ['electrical', 'electrical', 'power']):
        return 'electrical'
    elif any(term in work_type.lower() for term in ['civil', 'construction', 'building']):
        return 'civil'
    elif any(term in work_type.lower() for term in ['architectural', 'design', 'structure']):
        return 'architectural'
    elif any(term in work_type.lower() for term in ['mechanical', 'hvac', 'plumbing']):
        return 'mechanical'
    
    return 'general'


def create_scopes(project: ProjectProfile, divisions: List[Dict[str, Any]]) -> List[ProjectScope]:
    """
    Create ProjectScope entities from BOQ divisions.
    
    Args:
        project: ProjectProfile instance
        divisions: List of division items (level 0)
    
    Returns:
        List[ProjectScope]: Created scope objects
    """
    created_scopes = []
    
    for division in divisions:
        try:
            scope, created = ProjectScope.objects.get_or_create(
                project=project,
                name=division.get('division', 'General'),
                defaults={
                    'description': division.get('description', ''),
                    'weight': Decimal('0.0'),  # Will be calculated later
                    'status': 'pending'
                }
            )
            
            if created:
                created_scopes.append(scope)
                logger.info(f"Created scope: {scope.name} for project {project.id}")
            else:
                logger.info(f"Scope already exists: {scope.name} for project {project.id}")
                
        except Exception as e:
            logger.error(f"Error creating scope {division.get('division', 'Unknown')}: {e}")
    
    return created_scopes


def create_tasks(project: ProjectProfile, tasks: List[Dict[str, Any]], 
                 scopes: List[ProjectScope]) -> List[ProjectTask]:
    """
    Create ProjectTask entities from BOQ tasks.
    
    Args:
        project: ProjectProfile instance
        tasks: List of task items (level 1)
        scopes: List of created scopes to link tasks to
    
    Returns:
        List[ProjectTask]: Created task objects
    """
    created_tasks = []
    
    # Create a mapping of division names to scopes with fuzzy matching
    scope_map = {scope.name: scope for scope in scopes}
    
    def find_matching_scope(division_name):
        """Find the best matching scope for a division name"""
        # First try exact match
        if division_name in scope_map:
            return scope_map[division_name]
        
        # Try case-insensitive match
        for scope_name, scope in scope_map.items():
            if scope_name.lower() == division_name.lower():
                return scope
        
        # Try partial match
        for scope_name, scope in scope_map.items():
            if division_name.lower() in scope_name.lower() or scope_name.lower() in division_name.lower():
                return scope
        
        # If no match found, use the first available scope or create a default one
        if scopes:
            return scopes[0]  # Use first scope as fallback
        else:
            # Create a default scope if none exist
            default_scope, _ = ProjectScope.objects.get_or_create(
                project=project,
                name='General',
                defaults={
                    'weight': Decimal('0.0')
                }
            )
            return default_scope
    
    for task in tasks:
        try:
            # Find the appropriate scope for this task
            division = task.get('division', 'General')
            scope = find_matching_scope(division)
            
            task_obj, created = ProjectTask.objects.get_or_create(
                project=project,
                task_name=task.get('task', 'General Task'),
                scope=scope,
                defaults={
                    'description': task.get('description', ''),
                    'weight': Decimal('0.0'),  # Will be calculated later
                    'status': 'pending',
                    'start_date': project.start_date or timezone.now().date(),
                    'end_date': project.target_completion_date or (timezone.now().date() + timezone.timedelta(days=30))
                }
            )
            
            if created:
                created_tasks.append(task_obj)
                logger.info(f"Created task: {task_obj.task_name} for project {project.id}")
            else:
                logger.info(f"Task already exists: {task_obj.task_name} for project {project.id}")
                
        except Exception as e:
            logger.error(f"Error creating task {task.get('task', 'Unknown')}: {e}")
    
    return created_tasks


def create_line_items(project: ProjectProfile, line_items: List[Dict[str, Any]], 
                     tasks: List[ProjectTask]) -> Tuple[List[Any], List[Any], List[ProjectGeneralRequirement]]:
    """
    Create Material, Equipment, and MobilizationCost entities from BOQ line items.
    
    Args:
        project: ProjectProfile instance
        line_items: List of line items (level 2)
        tasks: List of created tasks to link items to
    
    Returns:
        Tuple: (materials, equipment, mobilization_costs)
    """
    materials = []
    equipment = []
    mobilization_costs = []
    
    # Create a mapping of task names to tasks
    task_map = {task.name: task for task in tasks}
    
    # Get project work type for classification
    work_type = get_project_work_type(project)
    
    for item in line_items:
        try:
            # Classify the item
            item_type = classify_boq_item(item, work_type)
            
            # Get the task for this item
            task_name = item.get('task', 'General Task')
            task = task_map.get(task_name)
            
            if item_type == 'mobilization':
                # Create MobilizationCost
                mob_cost = create_mobilization_cost(project, item, task)
                if mob_cost:
                    mobilization_costs.append(mob_cost)
                    
            elif item_type == 'equipment':
                # Create Equipment and ProjectEquipment
                equip = create_equipment(project, item, task, work_type)
                if equip:
                    equipment.append(equip)
                    
            else:  # material
                # Create Material and ProjectMaterial
                material = create_material(project, item, task, work_type)
                if material:
                    materials.append(material)
                    
        except Exception as e:
            logger.error(f"Error processing line item {item.get('description', 'Unknown')}: {e}")
    
    return materials, equipment, mobilization_costs


def create_mobilization_cost(project: ProjectProfile, item: Dict[str, Any], 
                           task: ProjectTask = None) -> ProjectGeneralRequirement:
    """
    Create a ProjectGeneralRequirement entity for mobilization costs.
    
    Args:
        project: ProjectProfile instance
        item: BOQ item data
        task: Associated task (optional)
    
    Returns:
        ProjectGeneralRequirement: Created mobilization cost object
    """
    try:
        # Determine category based on description
        description = item.get('description', '').lower()
        if 'mobilization' in description or 'setup' in description:
            category = 'Mobilization'
        elif 'engineer' in description or 'supervisor' in description:
            category = 'Personnel'
        else:
            category = 'Other'
        
        # Get or create the base GeneralRequirement
        requirement, created = GeneralRequirement.objects.get_or_create(
            name=item.get('description', 'Unknown Requirement'),
            defaults={
                'description': item.get('description', ''),
                'category': category,
                'unit_cost': Decimal(str(item.get('unit_cost', 0))),
                'unit': item.get('uom', 'unit')
            }
        )
        
        if created:
            logger.info(f"Created general requirement: {requirement.name}")
        
        # Create ProjectGeneralRequirement link
        project_requirement = ProjectGeneralRequirement.objects.create(
            project=project,
            requirement=requirement,
            quantity=Decimal(str(item.get('quantity', 1))),
            unit_cost=Decimal(str(item.get('unit_cost', 0))),
            notes=f"From BOQ - Task: {task.name if task else 'General'}"
        )
        
        logger.info(f"Created project general requirement: {requirement.name} for project {project.id}")
        return project_requirement
        
    except Exception as e:
        logger.error(f"Error creating mobilization cost: {e}")
        return None


def create_equipment(project: ProjectProfile, item: Dict[str, Any], 
                    task: ProjectTask = None, work_type: str = 'general') -> Any:
    """
    Create Equipment and ProjectEquipment entities.
    
    Args:
        project: ProjectProfile instance
        item: BOQ item data
        task: Associated task (optional)
        work_type: Project work type
    
    Returns:
        Equipment: Created equipment object
    """
    try:
        # Get or create the base Equipment
        equipment, created = Equipment.objects.get_or_create(
            name=item.get('description', 'Unknown Equipment'),
            defaults={
                'category': WORK_TYPE_CLASSIFICATIONS.get(work_type, {}).get('category', 'General'),
                'description': item.get('description', ''),
                'unit': item.get('uom', 'unit'),
                'standard_rate': Decimal(str(item.get('unit_cost', 0))),
                'is_active': True
            }
        )
        
        if created:
            logger.info(f"Created equipment: {equipment.name}")
        
        # Create ProjectEquipment link using the existing model structure
        project_equipment = ProjectEquipment.objects.create(
            project=project,
            equipment=equipment,
            quantity=Decimal(str(item.get('quantity', 1))),
            duration_days=30,  # Default duration
            unit_rate=Decimal(str(item.get('unit_cost', 0))),
            supplier_type='REG',  # Default to Regular Supplier
            supplier_name='BOQ Source',
            notes=f"From BOQ - Task: {task.name if task else 'General'}"
        )
        
        logger.info(f"Created project equipment link: {equipment.name} for project {project.id}")
        return equipment
        
    except Exception as e:
        logger.error(f"Error creating equipment: {e}")
        return None


def create_material(project: ProjectProfile, item: Dict[str, Any], 
                   task: ProjectTask = None, work_type: str = 'general') -> Any:
    """
    Create Material and ProjectMaterial entities.
    
    Args:
        project: ProjectProfile instance
        item: BOQ item data
        task: Associated task (optional)
        work_type: Project work type
    
    Returns:
        Material: Created material object
    """
    try:
        # Get or create the base Material
        material, created = Material.objects.get_or_create(
            name=item.get('description', 'Unknown Material'),
            defaults={
                'category': WORK_TYPE_CLASSIFICATIONS.get(work_type, {}).get('category', 'General'),
                'description': item.get('description', ''),
                'unit': item.get('uom', 'unit'),
                'standard_price': Decimal(str(item.get('unit_cost', 0))),
                'is_active': True
            }
        )
        
        if created:
            logger.info(f"Created material: {material.name}")
        
        # Create ProjectMaterial link using the existing model structure
        project_material = ProjectMaterial.objects.create(
            project=project,
            material=material,
            quantity=Decimal(str(item.get('quantity', 1))),
            unit_price=Decimal(str(item.get('unit_cost', 0))),
            supplier_type='REG',  # Default to Regular Supplier
            supplier_name='BOQ Source',
            notes=f"From BOQ - Task: {task.name if task else 'General'}"
        )
        
        logger.info(f"Created project material link: {material.name} for project {project.id}")
        return material
        
    except Exception as e:
        logger.error(f"Error creating material: {e}")
        return None


@transaction.atomic
def create_project_entities_from_boq(project: ProjectProfile) -> Dict[str, int]:
    """
    Main function to extract BOQ data and create all project entities.
    
    Args:
        project: ProjectProfile instance with BOQ data
    
    Returns:
        Dict[str, int]: Count of created entities
    """
    try:
        # Get BOQ data from project
        boq_items = getattr(project, 'boq_items', [])
        if not boq_items:
            logger.warning(f"Project {project.id} has no BOQ items")
            return {'error': 'No BOQ items found'}
        
        logger.info(f"Processing {len(boq_items)} BOQ items for project {project.id}")
        
        # Group items by hierarchy level based on code structure
        # No dots = SCOPES (divisions)
        # 1 dot = TASKS (subdivisions)  
        # 2 dots = MATERIALS/EQUIPMENT (line items)
        
        divisions = []
        tasks = []
        line_items = []
        
        for item in boq_items:
            code = item.get('code', '')
            level = item.get('level', 0)
            
            # Count dots in code to determine hierarchy
            dot_count = code.count('.')
            
            if dot_count == 0:  # No dots = SCOPES
                divisions.append(item)
            elif dot_count == 1:  # 1 dot = TASKS
                tasks.append(item)
            elif dot_count == 2:  # 2 dots = MATERIALS/EQUIPMENT
                line_items.append(item)
            else:
                # Fallback to level field if code doesn't follow pattern
                if level == 0:
                    divisions.append(item)
                elif level == 1:
                    tasks.append(item)
                else:
                    line_items.append(item)
        
        logger.info(f"Found {len(divisions)} divisions, {len(tasks)} tasks, {len(line_items)} line items")
        
        # Create entities
        scopes_created = create_scopes(project, divisions)
        
        # If no 1-dot tasks exist, create tasks from divisions
        if not tasks and divisions:
            logger.info("No 1-dot tasks found, creating tasks from divisions")
            tasks = []
            for division in divisions:
                # Create a task for each division
                task_data = {
                    'task': f"{division.get('division', 'General')} Implementation",
                    'description': f"Implementation of {division.get('division', 'General')} scope",
                    'division': division.get('division', 'General')
                }
                tasks.append(task_data)
        
        # Also create tasks from line items if they have task information
        if not tasks and line_items:
            logger.info("Creating tasks from line items")
            # Group line items by their task field
            task_groups = {}
            for item in line_items:
                task_name = item.get('task', 'General Implementation')
                if task_name not in task_groups:
                    task_groups[task_name] = {
                        'task': task_name,
                        'description': f"Implementation of {task_name}",
                        'division': item.get('division', 'General'),
                        'items': []
                    }
                task_groups[task_name]['items'].append(item)
            
            # Convert to task list
            tasks = list(task_groups.values())
            logger.info(f"Created {len(tasks)} tasks from line items")
        
        tasks_created = create_tasks(project, tasks, scopes_created)
        logger.info(f"Created {len(tasks_created)} tasks for project {project.id}")
        for task in tasks_created:
            logger.info(f"  - Task: {task.task_name} (Scope: {task.scope.name if task.scope else 'None'})")
        
        materials, equipment, mobilization_costs = create_line_items(project, line_items, tasks_created)
        
        result = {
            'scopes': len(scopes_created),
            'tasks': len(tasks_created),
            'materials': len(materials),
            'equipment': len(equipment),
            'mobilization_costs': len(mobilization_costs)
        }
        
        logger.info(f"Successfully created entities for project {project.id}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error creating project entities for project {project.id}: {e}")
        raise
