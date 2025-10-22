"""
Price monitoring integration for BOQ and Quotation material extraction
"""
import logging
from decimal import Decimal
from typing import List, Dict, Any, Optional
from django.db import transaction
from django.contrib.auth import get_user_model

from materials_equipment.models import Material, MaterialPriceMonitoring, ProjectMaterialExtraction
from project_profiling.models import ProjectProfile

logger = logging.getLogger(__name__)
User = get_user_model()


def create_price_records_from_boq(project: ProjectProfile, boq_items: List[Dict[str, Any]], 
                                extracted_by: Optional[Any] = None) -> Dict[str, int]:
    """
    Create price monitoring records from BOQ extraction data.
    
    Args:
        project: ProjectProfile instance
        boq_items: List of BOQ items with material data
        extracted_by: User who performed the extraction
    
    Returns:
        Dict with counts of created records
    """
    try:
        created_records = 0
        total_value = Decimal('0')
        
        # Create extraction tracking record
        extraction_record = ProjectMaterialExtraction.objects.create(
            project=project,
            source_type='BOQ',
            source_file=getattr(project, 'boq_file_name', 'BOQ File'),
            materials_count=0,
            equipment_count=0,
            mobilization_count=0,
            total_extracted_value=0,
            extraction_notes=f"BOQ extraction for project {project.project_name}",
            extracted_by=extracted_by
        )
        
        for item in boq_items:
            if item.get('level') == 2:  # Line items only
                material_name = item.get('description', '').strip()
                unit_cost = item.get('unit_cost', 0)
                quantity = item.get('quantity', 1)
                amount = item.get('amount', 0)
                
                if not material_name or not unit_cost:
                    continue
                
                # Find or create material
                material, created = Material.objects.get_or_create(
                    name=material_name,
                    defaults={
                        'description': f"Extracted from BOQ for {project.project_name}",
                        'unit': item.get('uom', 'unit'),
                        'standard_price': Decimal(str(unit_cost)),
                        'category': _classify_material_category(material_name),
                        'source': 'BOQ'
                    }
                )
                
                # Create price monitoring record
                price_record = MaterialPriceMonitoring.objects.create(
                    material=material,
                    supplier_type='BOQ',
                    supplier_name=f"BOQ - {project.project_name}",
                    price=Decimal(str(unit_cost)),
                    date=project.created_at.date(),
                    notes=f"BOQ estimate for {project.project_name}",
                    project=project,
                    recorded_by=extracted_by
                )
                
                created_records += 1
                total_value += Decimal(str(amount))
                
                # Update extraction counts
                if item.get('is_requirement', False):
                    extraction_record.mobilization_count += 1
                else:
                    extraction_record.materials_count += 1
        
        # Update extraction record with totals
        extraction_record.materials_count = created_records
        extraction_record.total_extracted_value = total_value
        extraction_record.save()
        
        logger.info(f"Created {created_records} BOQ price records for project {project.id}")
        return {
            'price_records': created_records,
            'total_value': float(total_value),
            'extraction_id': extraction_record.id
        }
        
    except Exception as e:
        logger.error(f"Error creating BOQ price records for project {project.id}: {e}")
        raise


def create_price_records_from_quotation(project: ProjectProfile, quotation_data: List[Dict[str, Any]], 
                                      extracted_by: Optional[Any] = None) -> Dict[str, int]:
    """
    Create price monitoring records from approved quotation data.
    
    Args:
        project: ProjectProfile instance
        quotation_data: List of quotation items with material data
        extracted_by: User who performed the extraction
    
    Returns:
        Dict with counts of created records
    """
    try:
        created_records = 0
        total_value = Decimal('0')
        
        # Create extraction tracking record
        extraction_record = ProjectMaterialExtraction.objects.create(
            project=project,
            source_type='QUOTATION',
            source_file=getattr(project, 'quotation_file_name', 'Quotation File'),
            materials_count=0,
            equipment_count=0,
            mobilization_count=0,
            total_extracted_value=0,
            extraction_notes=f"Quotation extraction for project {project.project_name}",
            extracted_by=extracted_by
        )
        
        for item in quotation_data:
            material_name = item.get('description', '').strip()
            unit_cost = item.get('unit_cost', 0)
            quantity = item.get('quantity', 1)
            amount = item.get('amount', 0)
            
            if not material_name or not unit_cost:
                continue
            
            # Find or create material
            material, created = Material.objects.get_or_create(
                name=material_name,
                defaults={
                    'description': f"Extracted from quotation for {project.project_name}",
                    'unit': item.get('uom', 'unit'),
                    'standard_price': Decimal(str(unit_cost)),
                    'category': _classify_material_category(material_name),
                    'source': 'QUOTATION'
                }
            )
            
            # Create price monitoring record
            price_record = MaterialPriceMonitoring.objects.create(
                material=material,
                supplier_type='QUOTATION',
                supplier_name=f"Quotation - {project.project_name}",
                price=Decimal(str(unit_cost)),
                date=project.created_at.date(),
                notes=f"Quotation price for {project.project_name}",
                project=project,
                recorded_by=extracted_by
            )
            
            created_records += 1
            total_value += Decimal(str(amount))
        
        # Update extraction record with totals
        extraction_record.materials_count = created_records
        extraction_record.total_extracted_value = total_value
        extraction_record.save()
        
        logger.info(f"Created {created_records} quotation price records for project {project.id}")
        return {
            'price_records': created_records,
            'total_value': float(total_value),
            'extraction_id': extraction_record.id
        }
        
    except Exception as e:
        logger.error(f"Error creating quotation price records for project {project.id}: {e}")
        raise


def _classify_material_category(material_name: str) -> str:
    """
    Classify material category based on name.
    
    Args:
        material_name: Name of the material
    
    Returns:
        str: Category classification
    """
    name_lower = material_name.lower()
    
    # Electrical materials
    if any(term in name_lower for term in ['cable', 'wire', 'conduit', 'outlet', 'switch', 'breaker', 'panel', 'electrical']):
        return 'ELECTRICAL'
    
    # Civil materials
    elif any(term in name_lower for term in ['concrete', 'cement', 'steel', 'rebar', 'block', 'brick', 'sand', 'gravel']):
        return 'CIVIL'
    
    # Mechanical materials
    elif any(term in name_lower for term in ['pipe', 'valve', 'pump', 'hvac', 'duct', 'mechanical']):
        return 'MECHANICAL'
    
    # Architectural materials
    elif any(term in name_lower for term in ['paint', 'tile', 'flooring', 'ceiling', 'door', 'window', 'architectural']):
        return 'ARCHITECTURAL'
    
    # General requirements
    elif any(term in name_lower for term in ['mobilization', 'temporary', 'safety', 'permit', 'supervision']):
        return 'GENERAL'
    
    return 'GENERAL'


def get_price_variance_analysis(project: ProjectProfile) -> Dict[str, Any]:
    """
    Get price variance analysis for a project.
    
    Args:
        project: ProjectProfile instance
    
    Returns:
        Dict with variance analysis data
    """
    try:
        # Get BOQ and Quotation price records for this project
        boq_records = MaterialPriceMonitoring.objects.filter(
            project=project,
            supplier_type='BOQ'
        )
        
        quotation_records = MaterialPriceMonitoring.objects.filter(
            project=project,
            supplier_type='QUOTATION'
        )
        
        variance_data = []
        total_boq_value = Decimal('0')
        total_quotation_value = Decimal('0')
        
        # Compare BOQ vs Quotation prices
        for boq_record in boq_records:
            quotation_record = quotation_records.filter(material=boq_record.material).first()
            
            if quotation_record:
                variance = quotation_record.price - boq_record.price
                variance_percentage = (variance / boq_record.price * 100) if boq_record.price > 0 else 0
                
                variance_data.append({
                    'material': boq_record.material.name,
                    'boq_price': float(boq_record.price),
                    'quotation_price': float(quotation_record.price),
                    'variance': float(variance),
                    'variance_percentage': float(variance_percentage)
                })
                
                total_boq_value += boq_record.price
                total_quotation_value += quotation_record.price
        
        overall_variance = total_quotation_value - total_boq_value
        overall_variance_percentage = (overall_variance / total_boq_value * 100) if total_boq_value > 0 else 0
        
        return {
            'project_name': project.project_name,
            'total_boq_value': float(total_boq_value),
            'total_quotation_value': float(total_quotation_value),
            'overall_variance': float(overall_variance),
            'overall_variance_percentage': float(overall_variance_percentage),
            'variance_details': variance_data,
            'record_count': len(variance_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting price variance analysis for project {project.id}: {e}")
        return {'error': str(e)}
