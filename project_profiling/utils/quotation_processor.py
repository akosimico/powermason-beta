"""
Quotation Processor Utility

This module handles processing of approved quotations to automatically create
project tasks, scopes, materials, and budget categories.
"""

import pandas as pd
from decimal import Decimal
from django.core.files.storage import default_storage
from io import BytesIO
from django.utils import timezone
from ..models import ProjectProfile, ProjectScope, ProjectBudget, CostCategory
from scheduling.models import ProjectTask
from materials_equipment.models import Material, Equipment


def extract_total_from_excel(quotation_file):
    """
    Extract total amount from Excel quotation file with enhanced parsing
    
    Args:
        quotation_file: FileField instance
        
    Returns:
        Decimal: Total amount extracted from file, or None if not found
    """
    try:
        # Read Excel file
        df = pd.read_excel(quotation_file)
        print(f"DEBUG: Excel file loaded with {len(df)} rows and columns: {list(df.columns)}")
        
        # Method 1: Look for "Amount" column specifically (most common in BOQ files)
        if 'Amount' in df.columns:
            print("DEBUG: Found 'Amount' column, checking for grand total...")
            amount_values = df['Amount'].dropna()
            if not amount_values.empty:
                # Strategy: Look for the last significant value (likely grand total)
                # Skip small values that are likely subtotals
                numeric_values = []
                for val in amount_values:
                    try:
                        if isinstance(val, (int, float)) and val > 0:
                            numeric_values.append(float(val))
                    except (ValueError, TypeError):
                        continue
                
                if numeric_values:
                    # Sort values to find the largest (most likely grand total)
                    sorted_values = sorted(numeric_values, reverse=True)
                    print(f"DEBUG: Found {len(sorted_values)} numeric values in Amount column: {sorted_values[:5]}...")
                    
                    # Look for the largest value that's significantly bigger than others
                    if len(sorted_values) > 1:
                        # Find the largest value that's at least 2x bigger than the second largest
                        largest = sorted_values[0]
                        second_largest = sorted_values[1]
                        
                        if largest >= second_largest * 2:
                            print(f"DEBUG: Found grand total {largest} (significantly larger than {second_largest})")
                            return Decimal(str(largest))
                        else:
                            # If no clear grand total, take the largest
                            print(f"DEBUG: No clear grand total, using largest value {largest}")
                            return Decimal(str(largest))
                    else:
                        # Only one value, use it
                        print(f"DEBUG: Only one value found: {sorted_values[0]}")
                        return Decimal(str(sorted_values[0]))
        
        # Method 2: Look for common total amount column names (case-insensitive)
        total_columns = [
            'total', 'total_amount', 'grand_total', 'amount', 'sum', 'total_cost',
            'subtotal', 'final_total', 'net_total', 'quotation_total', 'price_total',
            'cost_total', 'invoice_total', 'bill_total', 'charge_total'
        ]
        
        for col in total_columns:
            matching_cols = [c for c in df.columns if col.lower() in c.lower()]
            for match_col in matching_cols:
                print(f"DEBUG: Checking column '{match_col}' for total amount")
                # Get the last non-null value in the column
                total_values = df[match_col].dropna()
                if not total_values.empty:
                    # Try to find the largest numeric value (likely the total)
                    numeric_values = []
                    for val in total_values:
                        try:
                            if isinstance(val, (int, float)) and val > 0:
                                numeric_values.append(float(val))
                        except (ValueError, TypeError):
                            continue
                    
                    if numeric_values:
                        # Get the largest value (most likely to be the total)
                        total_amount = max(numeric_values)
                        print(f"DEBUG: Found total amount {total_amount} in column '{match_col}'")
                        return Decimal(str(total_amount))
        
        # Method 3: Look for cells containing "Total" or "TOTAL" in the same row
        print("DEBUG: Searching for 'Total' text in cells...")
        for idx, row in df.iterrows():
            for col in df.columns:
                cell_value = str(row[col]).lower()
                if 'total' in cell_value:
                    # Look for numeric values in adjacent cells
                    for adj_col in df.columns:
                        try:
                            adj_value = row[adj_col]
                            if isinstance(adj_value, (int, float)) and adj_value > 0:
                                print(f"DEBUG: Found total amount {adj_value} near 'Total' text")
                                return Decimal(str(adj_value))
                        except (ValueError, TypeError):
                            continue
        
        # Method 4: Look for grand total by analyzing Excel structure
        print("DEBUG: Analyzing Excel structure for grand total...")
        
        # Look for rows with "TOTAL" or "GRAND TOTAL" text and find the largest amount
        grand_totals = []
        subtotals = []
        
        for idx, row in df.iterrows():
            for col in df.columns:
                cell_value = str(row[col]).upper()
                if 'TOTAL' in cell_value or 'GRAND' in cell_value:
                    # Look for numeric values in the same row
                    for num_col in df.columns:
                        try:
                            if isinstance(row[num_col], (int, float)) and row[num_col] > 0:
                                total_info = {
                                    'value': float(row[num_col]),
                                    'row': idx,
                                    'col': num_col,
                                    'text': cell_value
                                }
                                
                                # Categorize as grand total or subtotal
                                if 'GRAND' in cell_value or 'FINAL' in cell_value or 'PROJECT' in cell_value:
                                    grand_totals.append(total_info)
                                    print(f"DEBUG: Found potential grand total {row[num_col]} in row {idx}, column {num_col} (text: {cell_value})")
                                else:
                                    subtotals.append(total_info)
                                    print(f"DEBUG: Found subtotal {row[num_col]} in row {idx}, column {num_col} (text: {cell_value})")
                        except (ValueError, TypeError):
                            continue
        
        # If we found explicit grand totals, use the largest
        if grand_totals:
            grand_totals.sort(key=lambda x: x['value'], reverse=True)
            largest_total = grand_totals[0]
            print(f"DEBUG: Selected grand total {largest_total['value']} from {len(grand_totals)} grand total entries")
            return Decimal(str(largest_total['value']))
        
        # If no explicit grand total, try to calculate from subtotals
        if subtotals:
            print(f"DEBUG: No explicit grand total found, analyzing {len(subtotals)} subtotals...")
            
            # Look for the largest subtotal (likely the grand total)
            subtotals.sort(key=lambda x: x['value'], reverse=True)
            
            # If the largest subtotal is significantly bigger than others, it's likely the grand total
            if len(subtotals) > 1:
                largest = subtotals[0]['value']
                second_largest = subtotals[1]['value']
                
                if largest >= second_largest * 10:  # 10x threshold for grand total
                    print(f"DEBUG: Largest subtotal {largest} is significantly larger than others, using as grand total")
                    return Decimal(str(largest))
                else:
                    # Sum all subtotals to get grand total
                    total_sum = sum(st['value'] for st in subtotals)
                    print(f"DEBUG: Summing all subtotals: {[st['value'] for st in subtotals]} = {total_sum}")
                    return Decimal(str(total_sum))
            else:
                # Only one subtotal, use it
                print(f"DEBUG: Only one subtotal found: {subtotals[0]['value']}")
                return Decimal(str(subtotals[0]['value']))
        
        # Method 5: Look for the first row with a very large number (likely the grand total)
        print("DEBUG: Looking for large numbers that might be grand total...")
        for idx, row in df.iterrows():
            for col in df.columns:
                try:
                    if isinstance(row[col], (int, float)) and row[col] > 1000000:  # Look for numbers > 1M
                        print(f"DEBUG: Found large number {row[col]} in row {idx}, column {col}")
                        return Decimal(str(row[col]))
                except (ValueError, TypeError):
                    continue
        
        # Method 6: Calculate grand total by summing individual line items
        print("DEBUG: Attempting to calculate grand total from individual line items...")
        
        # Look for Amount column and sum all non-zero values (excluding subtotal rows)
        if 'Amount' in df.columns:
            amount_values = []
            for idx, row in df.iterrows():
                amount_val = row['Amount']
                if pd.notna(amount_val) and isinstance(amount_val, (int, float)) and amount_val > 0:
                    # Check if this row is likely a subtotal (has "TOTAL" in any column)
                    is_subtotal = False
                    for col in df.columns:
                        if pd.notna(row[col]) and 'TOTAL' in str(row[col]).upper():
                            is_subtotal = True
                            break
                    
                    if not is_subtotal:
                        amount_values.append(float(amount_val))
                        print(f"DEBUG: Added line item amount {amount_val} from row {idx}")
            
            if amount_values:
                grand_total = sum(amount_values)
                print(f"DEBUG: Calculated grand total from {len(amount_values)} line items: {grand_total}")
                return Decimal(str(grand_total))
        
        # Method 7: Sum all numeric columns (last resort)
        print("DEBUG: Attempting to sum all numeric columns...")
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            # Try different strategies
            strategies = [
                # Strategy 1: Sum the last row
                lambda: sum(df.iloc[-1][col] for col in numeric_cols if pd.notna(df.iloc[-1][col])),
                # Strategy 2: Sum the second-to-last row (in case last row is empty)
                lambda: sum(df.iloc[-2][col] for col in numeric_cols if pd.notna(df.iloc[-2][col])) if len(df) > 1 else 0,
                # Strategy 3: Sum all values in numeric columns
                lambda: sum(df[col].sum() for col in numeric_cols if df[col].dtype in ['int64', 'float64']),
            ]
            
            for i, strategy in enumerate(strategies):
                try:
                    total = strategy()
                    if total > 0:
                        print(f"DEBUG: Found total amount {total} using strategy {i+1}")
                        return Decimal(str(total))
                except Exception as e:
                    print(f"DEBUG: Strategy {i+1} failed: {e}")
                    continue
        
        print("DEBUG: No total amount found in Excel file")
        return None
        
    except Exception as e:
        print(f"Error extracting total from Excel: {e}")
        return None


def create_tasks_from_approved_quotation(project, quotation):
    """
    Create project tasks, scopes, and materials from approved quotation
    
    Args:
        project: ProjectProfile instance
        quotation: SupplierQuotation instance
        
    Returns:
        dict: Summary of created items
    """
    try:
        created_items = {
            'scopes': 0,
            'tasks': 0,
            'materials': 0,
            'budgets': 0,
            'errors': []
        }
        
        # Use BOQ data if available, otherwise try to parse quotation file
        if project.boq_items:
            created_items = _create_from_boq_data(project, quotation)
        elif quotation.is_excel:
            created_items = _create_from_excel_quotation(project, quotation)
        else:
            # For PDF quotations, create basic structure
            created_items = _create_basic_structure(project, quotation)
        
        return created_items
        
    except Exception as e:
        return {
            'scopes': 0,
            'tasks': 0,
            'materials': 0,
            'budgets': 0,
            'errors': [f"Error creating items from quotation: {str(e)}"]
        }


def _create_from_boq_data(project, quotation):
    """Create items from BOQ data"""
    created_items = {
        'scopes': 0,
        'tasks': 0,
        'materials': 0,
        'budgets': 0,
        'errors': []
    }
    
    try:
        boq_items = project.boq_items
        if not boq_items:
            return created_items
        
        # Group items by division (scope)
        divisions = {}
        for item in boq_items:
            division = item.get('division', 'General Items')
            if division not in divisions:
                divisions[division] = []
            divisions[division].append(item)
        
        # Create scopes and tasks for each division
        for division_name, items in divisions.items():
            # Create or get scope
            scope, created = ProjectScope.objects.get_or_create(
                project=project,
                name=division_name,
                defaults={
                    'description': f"Scope for {division_name}",
                    'created_by': project.created_by
                }
            )
            if created:
                created_items['scopes'] += 1
            
            # Create tasks for this scope
            task_groups = {}
            for item in items:
                task_name = item.get('task', 'General Task')
                if task_name not in task_groups:
                    task_groups[task_name] = []
                task_groups[task_name].append(item)
            
            for task_name, task_items in task_groups.items():
                # Calculate task total cost
                task_total = sum(float(item.get('amount', 0)) for item in task_items)
                
                # Create task
                task = ProjectTask.objects.create(
                    project=project,
                    scope=scope,
                    name=task_name,
                    description=f"Task: {task_name}",
                    start_date=project.start_date or timezone.now().date(),
                    end_date=project.target_completion_date or timezone.now().date(),
                    progress=0,
                    weight=10,  # Default weight
                    created_by=project.created_by
                )
                created_items['tasks'] += 1
                
                # Create materials for this task
                for item in task_items:
                    if item.get('quantity', 0) > 0:
                        material = Material.objects.create(
                            name=item.get('description', 'Material Item'),
                            description=item.get('description', ''),
                            quantity=Decimal(str(item.get('quantity', 0))),
                            unit=item.get('uom', 'pcs'),
                            unit_cost=Decimal(str(item.get('unit_cost', 0))),
                            total_cost=Decimal(str(item.get('amount', 0))),
                            project=project,
                            task=task,
                            created_by=project.created_by
                        )
                        created_items['materials'] += 1
        
        # Create budget categories
        created_items['budgets'] = _create_budget_categories(project, quotation)
        
    except Exception as e:
        created_items['errors'].append(f"Error creating from BOQ data: {str(e)}")
    
    return created_items


def _create_from_excel_quotation(project, quotation):
    """Create items from Excel quotation file"""
    created_items = {
        'scopes': 0,
        'tasks': 0,
        'materials': 0,
        'budgets': 0,
        'errors': []
    }
    
    try:
        # Read Excel file
        df = pd.read_excel(quotation.quotation_file)
        
        # Try to identify columns
        description_col = None
        quantity_col = None
        unit_col = None
        unit_cost_col = None
        amount_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'description' in col_lower or 'item' in col_lower:
                description_col = col
            elif 'quantity' in col_lower or 'qty' in col_lower:
                quantity_col = col
            elif 'unit' in col_lower and 'cost' not in col_lower:
                unit_col = col
            elif 'unit' in col_lower and 'cost' in col_lower:
                unit_cost_col = col
            elif 'amount' in col_lower or 'total' in col_lower:
                amount_col = col
        
        if not description_col:
            created_items['errors'].append("Could not identify description column in Excel file")
            return created_items
        
        # Create a general scope
        scope, created = ProjectScope.objects.get_or_create(
            project=project,
            name="Quotation Items",
            defaults={
                'description': "Items from approved quotation",
                'created_by': project.created_by
            }
        )
        if created:
            created_items['scopes'] += 1
        
        # Create a general task
        task = ProjectTask.objects.create(
            project=project,
            scope=scope,
            name="Quotation Implementation",
            description="Implementation of approved quotation items",
            start_date=project.start_date or timezone.now().date(),
            end_date=project.target_completion_date or timezone.now().date(),
            progress=0,
            weight=100,
            created_by=project.created_by
        )
        created_items['tasks'] += 1
        
        # Create materials for each row
        for _, row in df.iterrows():
            if pd.isna(row.get(description_col)):
                continue
            
            description = str(row[description_col])
            quantity = float(row[quantity_col]) if quantity_col and not pd.isna(row.get(quantity_col)) else 1.0
            unit = str(row[unit_col]) if unit_col and not pd.isna(row.get(unit_col)) else 'pcs'
            unit_cost = float(row[unit_cost_col]) if unit_cost_col and not pd.isna(row.get(unit_cost_col)) else 0.0
            amount = float(row[amount_col]) if amount_col and not pd.isna(row.get(amount_col)) else quantity * unit_cost
            
            material = Material.objects.create(
                name=description[:100],  # Truncate if too long
                description=description,
                quantity=Decimal(str(quantity)),
                unit=unit,
                unit_cost=Decimal(str(unit_cost)),
                total_cost=Decimal(str(amount)),
                project=project,
                task=task,
                created_by=project.created_by
            )
            created_items['materials'] += 1
        
        # Create budget categories
        created_items['budgets'] = _create_budget_categories(project, quotation)
        
    except Exception as e:
        created_items['errors'].append(f"Error creating from Excel quotation: {str(e)}")
    
    return created_items


def _create_basic_structure(project, quotation):
    """Create basic project structure for PDF quotations"""
    created_items = {
        'scopes': 0,
        'tasks': 0,
        'materials': 0,
        'budgets': 0,
        'errors': []
    }
    
    try:
        # Create a general scope
        scope, created = ProjectScope.objects.get_or_create(
            project=project,
            name="Project Implementation",
            defaults={
                'description': "General project implementation scope",
                'created_by': project.created_by
            }
        )
        if created:
            created_items['scopes'] += 1
        
        # Create a general task
        task = ProjectTask.objects.create(
            project=project,
            scope=scope,
            name="Project Execution",
            description="Execute project based on approved quotation",
            start_date=project.start_date or timezone.now().date(),
            end_date=project.target_completion_date or timezone.now().date(),
            progress=0,
            weight=100,
            created_by=project.created_by
        )
        created_items['tasks'] += 1
        
        # Create budget categories
        created_items['budgets'] = _create_budget_categories(project, quotation)
        
    except Exception as e:
        created_items['errors'].append(f"Error creating basic structure: {str(e)}")
    
    return created_items


def _create_budget_categories(project, quotation):
    """Create budget categories based on quotation amount"""
    try:
        total_amount = quotation.total_amount
        if not total_amount:
            return 0
        
        # Create budget categories based on typical construction breakdown
        budget_breakdown = {
            'Materials': total_amount * Decimal('0.4'),  # 40%
            'Labor': total_amount * Decimal('0.3'),      # 30%
            'Equipment': total_amount * Decimal('0.1'),  # 10%
            'Subcontractor': total_amount * Decimal('0.1'),  # 10%
            'Other': total_amount * Decimal('0.1')       # 10%
        }
        
        created_budgets = 0
        
        # Get or create a general scope for budget
        scope, _ = ProjectScope.objects.get_or_create(
            project=project,
            name="Project Budget",
            defaults={
                'description': "Overall project budget allocation",
                'created_by': project.created_by
            }
        )
        
        for category_name, amount in budget_breakdown.items():
            if amount > 0:
                # Map to CostCategory choices
                category_code = 'MAT' if category_name == 'Materials' else \
                              'LAB' if category_name == 'Labor' else \
                              'EQP' if category_name == 'Equipment' else \
                              'SUB' if category_name == 'Subcontractor' else 'OTH'
                
                ProjectBudget.objects.create(
                    project=project,
                    scope=scope,
                    category=category_code,
                    planned_amount=amount,
                    created_by=project.created_by
                )
                created_budgets += 1
        
        return created_budgets
        
    except Exception as e:
        print(f"Error creating budget categories: {e}")
        return 0
