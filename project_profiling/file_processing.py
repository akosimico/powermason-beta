"""
File Processing and Data Extraction System
Handles PDF and Excel file parsing for project data extraction
"""

import os
import json
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

try:
    import PyPDF2
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PDF processing libraries not available. Install PyPDF2 and pdfplumber for PDF support.")

try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    logger.warning("Excel processing library not available. Install openpyxl for Excel support.")


class FileProcessor:
    """
    Main file processor for extracting project data from uploaded files
    """
    
    SUPPORTED_EXTENSIONS = ['.pdf', '.xlsx', '.xls']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, file: UploadedFile):
        self.file = file
        self.file_name = file.name
        self.file_size = file.size
        self.file_extension = os.path.splitext(file.name)[1].lower()
        
    def is_supported(self) -> bool:
        """Check if file type is supported"""
        return self.file_extension in self.SUPPORTED_EXTENSIONS
    
    def is_valid_size(self) -> bool:
        """Check if file size is within limits"""
        return self.file_size <= self.MAX_FILE_SIZE
    
    def extract_data(self) -> Dict[str, Any]:
        """
        Extract data from the uploaded file
        Returns a dictionary with extracted information
        """
        if not self.is_supported():
            return {
                'success': False,
                'error': f'Unsupported file type: {self.file_extension}',
                'data': {}
            }
        
        if not self.is_valid_size():
            return {
                'success': False,
                'error': f'File too large. Maximum size: {self.MAX_FILE_SIZE // (1024*1024)}MB',
                'data': {}
            }
        
        try:
            if self.file_extension == '.pdf':
                return self._extract_from_pdf()
            elif self.file_extension in ['.xlsx', '.xls']:
                return self._extract_from_excel()
            else:
                return {
                    'success': False,
                    'error': 'Unsupported file format',
                    'data': {}
                }
        except Exception as e:
            logger.error(f"Error processing file {self.file_name}: {str(e)}")
            return {
                'success': False,
                'error': f'Error processing file: {str(e)}',
                'data': {}
            }
    
    def _extract_from_pdf(self) -> Dict[str, Any]:
        """Extract data from PDF files"""
        if not PDF_AVAILABLE:
            return {
                'success': False,
                'error': 'PDF processing not available. Please install required libraries.',
                'data': {}
            }
        
        try:
            # Reset file pointer
            self.file.seek(0)
            
            extracted_data = {
                'file_type': 'pdf',
                'file_name': self.file_name,
                'file_size': self.file_size,
                'text_content': '',
                'tables': [],
                'project_data': {
                    'tasks': [],
                    'costs': [],
                    'schedule': [],
                    'materials': [],
                    'equipment': []
                }
            }
            
            # Try pdfplumber first (better for tables)
            try:
                with pdfplumber.open(self.file) as pdf:
                    full_text = ""
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            full_text += page_text + "\n"
                        
                        # Extract tables
                        tables = page.extract_tables()
                        for table in tables:
                            if table and len(table) > 1:  # Skip empty tables
                                extracted_data['tables'].append({
                                    'page': pdf.pages.index(page) + 1,
                                    'data': table
                                })
                    
                    extracted_data['text_content'] = full_text
                    
            except Exception as e:
                logger.warning(f"pdfplumber failed, trying PyPDF2: {str(e)}")
                # Fallback to PyPDF2
                self.file.seek(0)
                pdf_reader = PyPDF2.PdfReader(self.file)
                full_text = ""
                for page in pdf_reader.pages:
                    full_text += page.extract_text() + "\n"
                extracted_data['text_content'] = full_text
            
            # Parse extracted text for project data
            extracted_data['project_data'] = self._parse_text_for_project_data(extracted_data['text_content'])
            
            return {
                'success': True,
                'data': extracted_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error reading PDF: {str(e)}',
                'data': {}
            }
    
    def _extract_from_excel(self) -> Dict[str, Any]:
        """Extract data from Excel files"""
        if not EXCEL_AVAILABLE:
            return {
                'success': False,
                'error': 'Excel processing not available. Please install openpyxl.',
                'data': {}
            }
        
        try:
            # Reset file pointer
            self.file.seek(0)
            
            extracted_data = {
                'file_type': 'excel',
                'file_name': self.file_name,
                'file_size': self.file_size,
                'sheets': [],
                'project_data': {
                    'tasks': [],
                    'costs': [],
                    'schedule': [],
                    'materials': [],
                    'equipment': []
                }
            }
            
            # Read Excel file
            excel_file = pd.ExcelFile(self.file)
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(self.file, sheet_name=sheet_name)
                
                # Convert DataFrame to list of dictionaries
                sheet_data = {
                    'name': sheet_name,
                    'data': df.to_dict('records'),
                    'columns': list(df.columns),
                    'row_count': len(df)
                }
                
                extracted_data['sheets'].append(sheet_data)
                
                # Try to identify project data based on sheet name and content
                self._parse_excel_sheet_for_project_data(sheet_name, df, extracted_data['project_data'])
            
            return {
                'success': True,
                'data': extracted_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error reading Excel file: {str(e)}',
                'data': {}
            }
    
    def _parse_text_for_project_data(self, text: str) -> Dict[str, List]:
        """Parse text content to extract project-related data"""
        project_data = {
            'tasks': [],
            'costs': [],
            'schedule': [],
            'materials': [],
            'equipment': []
        }
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for task patterns
            if any(keyword in line.lower() for keyword in ['task', 'activity', 'work', 'phase']):
                if ':' in line or '-' in line:
                    project_data['tasks'].append({
                        'description': line,
                        'type': 'task'
                    })
            
            # Look for cost patterns
            if any(keyword in line.lower() for keyword in ['cost', 'price', 'amount', 'budget', '₱', 'php', 'peso']):
                # Try to extract numbers
                import re
                numbers = re.findall(r'[\d,]+\.?\d*', line)
                if numbers:
                    project_data['costs'].append({
                        'description': line,
                        'amount': numbers[0],
                        'type': 'cost'
                    })
            
            # Look for material patterns
            if any(keyword in line.lower() for keyword in ['material', 'supply', 'cement', 'steel', 'lumber', 'concrete']):
                project_data['materials'].append({
                    'description': line,
                    'type': 'material'
                })
            
            # Look for equipment patterns
            if any(keyword in line.lower() for keyword in ['equipment', 'machine', 'tool', 'excavator', 'crane', 'bulldozer']):
                project_data['equipment'].append({
                    'description': line,
                    'type': 'equipment'
                })
        
        return project_data
    
    def _parse_excel_sheet_for_project_data(self, sheet_name: str, df: pd.DataFrame, project_data: Dict):
        """Parse Excel sheet to extract project data based on sheet name and content"""
        sheet_name_lower = sheet_name.lower()
        
        # Identify sheet type and extract relevant data
        if any(keyword in sheet_name_lower for keyword in ['task', 'activity', 'schedule', 'work']):
            # Extract tasks/schedule data
            for _, row in df.iterrows():
                if not row.isna().all():  # Skip empty rows
                    task_data = {
                        'description': str(row.iloc[0]) if len(row) > 0 else '',
                        'type': 'task'
                    }
                    
                    # Try to extract additional information
                    if len(row) > 1:
                        task_data['details'] = str(row.iloc[1])
                    if len(row) > 2:
                        task_data['notes'] = str(row.iloc[2])
                    
                    project_data['tasks'].append(task_data)
        
        elif any(keyword in sheet_name_lower for keyword in ['cost', 'budget', 'price', 'financial']):
            # Extract cost data
            for _, row in df.iterrows():
                if not row.isna().all():
                    cost_data = {
                        'description': str(row.iloc[0]) if len(row) > 0 else '',
                        'type': 'cost'
                    }
                    
                    # Try to find amount column
                    for col in df.columns:
                        if any(keyword in str(col).lower() for keyword in ['amount', 'cost', 'price', 'value']):
                            if col in row and pd.notna(row[col]):
                                cost_data['amount'] = str(row[col])
                                break
                    
                    project_data['costs'].append(cost_data)
        
        elif any(keyword in sheet_name_lower for keyword in ['material', 'supply', 'inventory']):
            # Extract material data
            for _, row in df.iterrows():
                if not row.isna().all():
                    material_data = {
                        'description': str(row.iloc[0]) if len(row) > 0 else '',
                        'type': 'material'
                    }
                    
                    # Try to extract quantity and unit
                    for col in df.columns:
                        col_lower = str(col).lower()
                        if 'quantity' in col_lower or 'qty' in col_lower:
                            if col in row and pd.notna(row[col]):
                                material_data['quantity'] = str(row[col])
                        elif 'unit' in col_lower:
                            if col in row and pd.notna(row[col]):
                                material_data['unit'] = str(row[col])
                    
                    project_data['materials'].append(material_data)
        
        elif any(keyword in sheet_name_lower for keyword in ['equipment', 'machine', 'tool']):
            # Extract equipment data
            for _, row in df.iterrows():
                if not row.isna().all():
                    equipment_data = {
                        'description': str(row.iloc[0]) if len(row) > 0 else '',
                        'type': 'equipment'
                    }
                    
                    project_data['equipment'].append(equipment_data)


class ProjectDataExtractor:
    """
    Advanced project data extraction and mapping
    """
    
    @staticmethod
    def extract_and_map_data(file_processor: FileProcessor) -> Dict[str, Any]:
        """
        Extract data from file and map it to project models
        """
        extraction_result = file_processor.extract_data()
        
        if not extraction_result['success']:
            return extraction_result
        
        raw_data = extraction_result['data']
        mapped_data = {
            'file_info': {
                'name': raw_data['file_name'],
                'type': raw_data['file_type'],
                'size': raw_data['file_size']
            },
            'extracted_content': raw_data,
            'mapped_models': {
                'tasks': [],
                'budgets': [],
                'materials': [],
                'equipment': [],
                'manpower': []
            },
            'preview': {
                'summary': '',
                'suggestions': []
            }
        }
        
        # Map extracted data to model structures
        ProjectDataExtractor._map_tasks(raw_data, mapped_data['mapped_models'])
        ProjectDataExtractor._map_costs(raw_data, mapped_data['mapped_models'])
        ProjectDataExtractor._map_materials(raw_data, mapped_data['mapped_models'])
        ProjectDataExtractor._map_equipment(raw_data, mapped_data['mapped_models'])
        
        # Generate preview and suggestions
        ProjectDataExtractor._generate_preview(mapped_data)
        
        return {
            'success': True,
            'data': mapped_data
        }
    
    @staticmethod
    def _map_tasks(raw_data: Dict, mapped_models: Dict):
        """Map extracted data to task model structure"""
        tasks = raw_data.get('project_data', {}).get('tasks', [])
        
        for task in tasks:
            mapped_task = {
                'task_name': task.get('description', '')[:255],  # Truncate to fit model field
                'description': task.get('details', ''),
                'notes': task.get('notes', ''),
                'suggested_duration': 7,  # Default 7 days
                'suggested_weight': 10,   # Default 10% weight
                'status': 'PL'  # Planned
            }
            mapped_models['tasks'].append(mapped_task)
    
    @staticmethod
    def _map_costs(raw_data: Dict, mapped_models: Dict):
        """Map extracted data to budget/cost model structure"""
        costs = raw_data.get('project_data', {}).get('costs', [])
        
        for cost in costs:
            mapped_cost = {
                'description': cost.get('description', '')[:255],
                'amount': cost.get('amount', '0'),
                'category': 'MAT',  # Default to Materials
                'notes': ''
            }
            mapped_models['budgets'].append(mapped_cost)
    
    @staticmethod
    def _map_materials(raw_data: Dict, mapped_models: Dict):
        """Map extracted data to material model structure"""
        materials = raw_data.get('project_data', {}).get('materials', [])
        
        for material in materials:
            mapped_material = {
                'name': material.get('description', '')[:255],
                'quantity': material.get('quantity', '1'),
                'unit': material.get('unit', 'pcs'),
                'notes': ''
            }
            mapped_models['materials'].append(mapped_material)
    
    @staticmethod
    def _map_equipment(raw_data: Dict, mapped_models: Dict):
        """Map extracted data to equipment model structure"""
        equipment = raw_data.get('project_data', {}).get('equipment', [])
        
        for eq in equipment:
            mapped_equipment = {
                'name': eq.get('description', '')[:255],
                'quantity': 1,
                'notes': ''
            }
            mapped_models['equipment'].append(mapped_equipment)
    
    @staticmethod
    def _generate_preview(mapped_data: Dict):
        """Generate preview summary and suggestions"""
        models = mapped_data['mapped_models']
        
        # Count items
        task_count = len(models['tasks'])
        cost_count = len(models['budgets'])
        material_count = len(models['materials'])
        equipment_count = len(models['equipment'])
        
        # Generate summary
        summary_parts = []
        if task_count > 0:
            summary_parts.append(f"{task_count} task(s)")
        if cost_count > 0:
            summary_parts.append(f"{cost_count} cost item(s)")
        if material_count > 0:
            summary_parts.append(f"{material_count} material(s)")
        if equipment_count > 0:
            summary_parts.append(f"{equipment_count} equipment item(s)")
        
        mapped_data['preview']['summary'] = f"Found: {', '.join(summary_parts)}"
        
        # Generate suggestions
        suggestions = []
        if task_count > 0:
            suggestions.append("Tasks can be automatically added to the project schedule")
        if cost_count > 0:
            suggestions.append("Cost items can be added to the project budget")
        if material_count > 0:
            suggestions.append("Materials can be added to the project materials list")
        if equipment_count > 0:
            suggestions.append("Equipment can be added to the project equipment list")
        
        if not suggestions:
            suggestions.append("No recognizable project data found. You can still upload the file for reference.")
        
        mapped_data['preview']['suggestions'] = suggestions


def extract_from_standard_template(excel_file) -> Dict[str, Any]:
    """
    Extract data from company standard BOQ template
    """
    try:
        # Read the single sheet
        df = pd.read_excel(excel_file, header=None)
        
        # Debug: Print basic info about the file
        print(f"DEBUG: Template file shape: {df.shape}")
        print(f"DEBUG: First few rows:\n{df.head()}")
        
        # Extract project information from new template format (rows 1-16)
        project_info = {
            'project_name': _get_cell_value(df, 'B1'),      # Project Name
            'project_type': _get_cell_value(df, 'B2'),      # Project Type
            'location': _get_cell_value(df, 'B3'),          # Location
            'client': _get_cell_value(df, 'B4'),            # Client
            'contractor': _get_cell_value(df, 'B5'),        # Contractor
            'proposal_no': _get_cell_value(df, 'B6'),       # Proposal No
            'lot_size': _get_cell_value(df, 'B7'),          # Lot Size (sqm)
            'floor_area': _get_cell_value(df, 'B8'),        # Floor Area (sqm)
            'project_category': _get_cell_value(df, 'B9'),  # Project Category
            'complexity_level': _get_cell_value(df, 'B10'), # Complexity Level
            'role_type': _get_cell_value(df, 'B11'),        # Role/Type
            'date_prepared': _get_cell_value(df, 'B12'),    # Date Prepared
            'prepared_by': _get_cell_value(df, 'B13'),      # Prepared By
        }
        
        # Extract BOQ items starting from row 20 (new template format)
        boq_items = extract_company_boq_items(df, start_row=19)
        
        # Calculate totals from BOQ items
        total_cost = sum(item.get('total_cost', Decimal('0')) for item in boq_items)
        materials_cost = sum(item.get('material_cost', Decimal('0')) for item in boq_items)
        labor_cost = sum(item.get('labor_cost', Decimal('0')) for item in boq_items)
        equipment_cost = sum(item.get('equipment_cost', Decimal('0')) for item in boq_items)
        subcontractor_cost = sum(item.get('subcontractor_cost', Decimal('0')) for item in boq_items)
        
        # Convert lot_size to proper type
        lot_size = Decimal(str(project_info.get('lot_size', 0))) if project_info.get('lot_size') else Decimal('0')
        
        # Calculate cost per sqm
        if lot_size > 0:
            cost_per_sqm = total_cost / lot_size
        else:
            cost_per_sqm = Decimal('0')
        
        # Calculate other costs as percentages
        permits_cost = total_cost * Decimal('0.05')  # 5% of total
        contingency_cost = total_cost * Decimal('0.10')  # 10% of total
        overhead_cost = total_cost * Decimal('0.05')  # 5% of total
        
        return {
            'success': True,
            'project_info': project_info,
            'boq_items': boq_items,
            'total_cost': total_cost,
            'lot_size': lot_size,
            'cost_per_sqm': cost_per_sqm,
            'floor_area': Decimal(str(project_info.get('floor_area', 0))) if project_info.get('floor_area') else Decimal('0'),
            'materials_cost': materials_cost,
            'labor_cost': labor_cost,
            'equipment_cost': equipment_cost,
            'subcontractor_cost': subcontractor_cost,
            'permits_cost': permits_cost,
            'contingency_cost': contingency_cost,
            'overhead_cost': overhead_cost,
            'location': project_info.get('location', ''),
            'project_type': project_info.get('project_type', 'Commercial'),
            'project_category': project_info.get('project_category', 'PRI'),
            'complexity_level': project_info.get('complexity_level', 'Mid Range').lower().replace(' ', '_'),
            'role': project_info.get('role_type', 'general_contractor')
        }
        
    except Exception as e:
        logger.error(f"Error extracting from company template: {str(e)}")
        return {
            'success': False,
            'error': f"Failed to extract data from company template: {str(e)}"
        }


def parse_dependencies(dependency_str: str) -> List[int]:
    """
    Parse dependency string and return list of item numbers
    Handles formats: "1,3,5", "Item 1, Item 3", "1,3", etc.
    """
    if not dependency_str or pd.isna(dependency_str):
        return []
    
    dependencies = []
    dependency_str = str(dependency_str).strip()
    
    # Split by comma and clean up
    parts = [part.strip() for part in dependency_str.split(',')]
    
    for part in parts:
        # Remove "Item" prefix if present
        if part.lower().startswith('item'):
            part = part[4:].strip()
        
        # Extract number
        try:
            item_num = int(part)
            dependencies.append(item_num)
        except ValueError:
            # Try to extract number from string
            import re
            numbers = re.findall(r'\d+', part)
            if numbers:
                dependencies.append(int(numbers[0]))
    
    return dependencies


def extract_company_boq_items(df: pd.DataFrame, start_row: int = 19) -> List[Dict[str, Any]]:
    """
    Extract BOQ items from company standard format (new template)
    Args:
        df: DataFrame containing the BOQ data
        start_row: Starting row index (0-based) for BOQ items. Default is 19 (row 20)
    """
    boq_items = []
    
    # Start from specified row and go until we find empty rows or "TOTAL"
    for row_idx in range(start_row, len(df)):
        # Check if this is a total row or empty row
        item_num = _get_cell_value(df, f'A{row_idx + 1}')
        description = _get_cell_value(df, f'B{row_idx + 1}')
        
        if pd.isna(item_num) or str(item_num).upper() in ['TOTAL', 'GRAND TOTAL', '']:
            break
        
        # Skip section headers (rows with description but no item number)
        if pd.isna(item_num) or str(item_num).strip() == '':
            continue
        
        # Skip subtotal rows
        if 'subtotal' in str(description).lower():
            continue
        
        try:
            # Extract item data from new template format
            item = {
                'item_number': int(item_num) if not pd.isna(item_num) else 0,
                'description': str(description) or '',
                'section': _get_cell_value(df, f'C{row_idx + 1}') or '',
                'uom': _get_cell_value(df, f'D{row_idx + 1}') or '',
                'quantity': Decimal(str(_get_cell_value(df, f'E{row_idx + 1}') or 0)),
                'unit_cost': Decimal(str(_get_cell_value(df, f'F{row_idx + 1}') or 0)),
                'total_cost': Decimal(str(_get_cell_value(df, f'G{row_idx + 1}') or 0)),
                'material_cost': Decimal(str(_get_cell_value(df, f'H{row_idx + 1}') or 0)),
                'labor_cost': Decimal(str(_get_cell_value(df, f'I{row_idx + 1}') or 0)),
                'equipment_cost': Decimal(str(_get_cell_value(df, f'J{row_idx + 1}') or 0)),
                'subcontractor_cost': Decimal(str(_get_cell_value(df, f'K{row_idx + 1}') or 0)),
                'dependencies': parse_dependencies(_get_cell_value(df, f'L{row_idx + 1}')),
                'remarks': _get_cell_value(df, f'M{row_idx + 1}') or ''
            }
            
            # Skip if no quantity or costs
            if item['quantity'] == 0 and item['total_cost'] == 0:
                continue
            
            # Calculate total cost if not provided
            if item['total_cost'] == 0 and item['quantity'] > 0 and item['unit_cost'] > 0:
                item['total_cost'] = item['quantity'] * item['unit_cost']
            
            boq_items.append(item)
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing company BOQ item at row {row_idx + 1}: {e}")
            continue
    
    return boq_items


def extract_detailed_boq_items(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Extract detailed BOQ items from the template starting at row 17
    """
    boq_items = []
    
    # Start from row 17 (index 16) and go until we find empty rows or "TOTAL"
    for row_idx in range(17, len(df)):
        # Check if this is a total row or empty row
        item_num = _get_cell_value(df, f'A{row_idx + 1}')
        if pd.isna(item_num) or str(item_num).upper() in ['TOTAL', 'GRAND TOTAL', '']:
            break
        
        # Skip section headers (rows with description but no item number)
        if pd.isna(item_num) or str(item_num).strip() == '':
            continue
        
        try:
            # Extract item data
            item = {
                'item_number': int(item_num) if not pd.isna(item_num) else 0,
                'description': _get_cell_value(df, f'B{row_idx + 1}') or '',
                'section': _get_cell_value(df, f'C{row_idx + 1}') or '',
                'uom': _get_cell_value(df, f'D{row_idx + 1}') or '',
                'quantity': Decimal(str(_get_cell_value(df, f'E{row_idx + 1}') or 0)),
                'unit_cost': Decimal(str(_get_cell_value(df, f'F{row_idx + 1}') or 0)),
                'total_cost': Decimal(str(_get_cell_value(df, f'G{row_idx + 1}') or 0)),
                'material_cost': Decimal(str(_get_cell_value(df, f'H{row_idx + 1}') or 0)),
                'labor_cost': Decimal(str(_get_cell_value(df, f'I{row_idx + 1}') or 0)),
                'equipment_cost': Decimal(str(_get_cell_value(df, f'J{row_idx + 1}') or 0)),
                'subcontractor_cost': Decimal(str(_get_cell_value(df, f'K{row_idx + 1}') or 0)),
                'dependencies': parse_dependencies(_get_cell_value(df, f'L{row_idx + 1}')),
                'remarks': _get_cell_value(df, f'M{row_idx + 1}') or ''
            }
            
            # Calculate total cost if not provided
            if item['total_cost'] == 0 and item['quantity'] > 0 and item['unit_cost'] > 0:
                item['total_cost'] = item['quantity'] * item['unit_cost']
            
            boq_items.append(item)
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing BOQ item at row {row_idx + 1}: {e}")
            continue
    
    return boq_items


def _get_cell_value(df: pd.DataFrame, cell_ref: str) -> Any:
    """
    Get value from specific cell reference (e.g., 'B2')
    """
    try:
        # Convert cell reference to row/col indices
        col = ord(cell_ref[0]) - ord('A')  # A=0, B=1, etc.
        row = int(cell_ref[1:]) - 1  # Convert to 0-based index
        
        if row < len(df) and col < len(df.columns):
            value = df.iloc[row, col]
            # Handle NaN values
            if pd.isna(value):
                return None
            return value
        return None
    except Exception:
        return None


def extract_cost_summary(file_content: bytes, file_extension: str) -> Dict[str, Any]:
    """
    Enhanced cost extraction with standard template support
    """
    if file_extension.lower() in ['.xlsx', '.xls']:
        try:
            # First try standard template
            result = extract_from_standard_template(file_content)
            if result.get('success'):
                return result
        except Exception as e:
            logger.warning(f"Standard template extraction failed: {e}")
        
        # Fallback to intelligent extraction
        return _extract_from_excel_intelligent(file_content)
    
    elif file_extension.lower() == '.pdf':
        return _extract_from_pdf_intelligent(file_content)
    
    return {
        'success': False,
        'error': 'Unsupported file type'
    }


def _extract_from_excel_intelligent(file_content: bytes) -> Dict[str, Any]:
    """
    Intelligent extraction from non-standard Excel files
    """
    try:
        # Read all sheets
        excel_file = pd.ExcelFile(file_content)
        
        total_cost = Decimal('0')
        lot_size = Decimal('0')
        cost_breakdown = {}
        
        # Look for cost-related keywords in all sheets
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_content, sheet_name=sheet_name)
            
            # Search for total cost
            for col in df.columns:
                for idx, value in df[col].items():
                    if pd.notna(value):
                        value_str = str(value).lower()
                        if any(keyword in value_str for keyword in ['total', 'grand total', 'subtotal']):
                            # Try to find numeric value in same row
                            for col2 in df.columns:
                                if pd.notna(df[col2].iloc[idx]):
                                    try:
                                        cost_val = Decimal(str(df[col2].iloc[idx]))
                                        if cost_val > total_cost:
                                            total_cost = cost_val
                                    except:
                                        pass
            
            # Search for lot size
            for col in df.columns:
                for idx, value in df[col].items():
                    if pd.notna(value):
                        value_str = str(value).lower()
                        if any(keyword in value_str for keyword in ['lot size', 'floor area', 'area']):
                            # Try to find numeric value
                            for col2 in df.columns:
                                if pd.notna(df[col2].iloc[idx]):
                                    try:
                                        size_val = Decimal(str(df[col2].iloc[idx]))
                                        if size_val > lot_size:
                                            lot_size = size_val
                                    except:
                                        pass
        
        cost_per_sqm = total_cost / lot_size if lot_size > 0 else Decimal('0')
        
        return {
            'success': True,
            'total_cost': total_cost,
            'lot_size': lot_size,
            'cost_per_sqm': cost_per_sqm,
            'materials_cost': Decimal('0'),
            'labor_cost': Decimal('0'),
            'equipment_cost': Decimal('0'),
            'permits_cost': Decimal('0'),
            'contingency_cost': Decimal('0'),
            'overhead_cost': Decimal('0'),
            'location': '',
            'project_category': 'PRI',
            'complexity_level': 'mid_range'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Failed to extract from Excel: {str(e)}"
        }


def _extract_from_pdf_intelligent(file_content: bytes) -> Dict[str, Any]:
    """
    Intelligent extraction from PDF files
    """
    if not PDF_AVAILABLE:
        return {
            'success': False,
            'error': 'PDF processing not available'
        }
    
    try:
        # Use pdfplumber for better text extraction
        import io
        pdf_file = io.BytesIO(file_content)
        
        total_cost = Decimal('0')
        lot_size = Decimal('0')
        
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # Look for cost patterns
                    cost_patterns = [
                        r'total[:\s]*₱?[\s]*([\d,]+\.?\d*)',
                        r'grand total[:\s]*₱?[\s]*([\d,]+\.?\d*)',
                        r'subtotal[:\s]*₱?[\s]*([\d,]+\.?\d*)'
                    ]
                    
                    for pattern in cost_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        for match in matches:
                            try:
                                cost_val = Decimal(match.replace(',', ''))
                                if cost_val > total_cost:
                                    total_cost = cost_val
                            except:
                                pass
                    
                    # Look for lot size patterns
                    size_patterns = [
                        r'lot size[:\s]*([\d,]+\.?\d*)\s*sqm',
                        r'floor area[:\s]*([\d,]+\.?\d*)\s*sqm',
                        r'area[:\s]*([\d,]+\.?\d*)\s*sqm'
                    ]
                    
                    for pattern in size_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        for match in matches:
                            try:
                                size_val = Decimal(match.replace(',', ''))
                                if size_val > lot_size:
                                    lot_size = size_val
                            except:
                                pass
        
        cost_per_sqm = total_cost / lot_size if lot_size > 0 else Decimal('0')
        
        return {
            'success': True,
            'total_cost': total_cost,
            'lot_size': lot_size,
            'cost_per_sqm': cost_per_sqm,
            'materials_cost': Decimal('0'),
            'labor_cost': Decimal('0'),
            'equipment_cost': Decimal('0'),
            'permits_cost': Decimal('0'),
            'contingency_cost': Decimal('0'),
            'overhead_cost': Decimal('0'),
            'location': '',
            'project_category': 'PRI',
            'complexity_level': 'mid_range'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Failed to extract from PDF: {str(e)}"
        }
