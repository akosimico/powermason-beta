# manage_client/xero_sync.py (create this new file)
from .xero_helpers import make_xero_api_call
from django.contrib import messages
import logging
from django.utils import timezone
from datetime import timedelta
from xero.xero_helpers import has_xero_connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from manage_client.models import Client
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)

def sync_client_to_xero(request, client):
    """
    Sync a Django client to Xero as a contact
    """
    if not has_xero_connection(request.user):
        return {'success': False, 'error': 'Not connected to Xero'}
    
    # Prepare contact data for Xero - use correct field names
    contact_data = {
        "Contacts": [{
            "Name": client.company_name,
            "FirstName": client.contact_name.split(' ')[0] if client.contact_name else '',
            "LastName": ' '.join(client.contact_name.split(' ')[1:]) if client.contact_name and len(client.contact_name.split(' ')) > 1 else '',
            "EmailAddress": client.email or '',
            "ContactNumber": f"CLIENT-{client.id}",
            "ContactStatus": "ACTIVE" if client.is_active else "INACTIVE",
            "Addresses": [{
                "AddressType": "STREET",
                "AddressLine1": client.address or '',  # Use correct field name
                "City": client.city or '',             # Use correct field name
                "Region": client.state or '',          # Use correct field name
                "PostalCode": client.zip_code or '',   # Use correct field name
            }] if client.address else [],
            "Phones": [{
                "PhoneType": "DEFAULT",
                "PhoneNumber": client.phone
            }] if client.phone else []
        }]
    }
    
    # Remove empty addresses if no address data
    if not client.address:
        contact_data["Contacts"][0].pop("Addresses", None)
    
    # Remove empty phones if no phone data
    if not client.phone:
        contact_data["Contacts"][0].pop("Phones", None)
    
    print("DEBUG: Xero contact data being sent:")
    print(contact_data)
    
    # Make API call to create contact
    result = make_xero_api_call(request, 'Contacts', method='POST', data=contact_data)
    
    print("DEBUG: Xero API result:")
    print(result)
    
    if result.get('success'):
        xero_contact = result['data']['Contacts'][0]
        
        # Store Xero contact ID in your client model
        client.xero_contact_id = xero_contact['ContactID']
        client.xero_last_sync = timezone.now()
        client.save()
        
        print(f"SUCCESS: Client {client.id} synced to Xero with ID: {xero_contact['ContactID']}")
        return {
            'success': True,
            'xero_contact_id': xero_contact['ContactID'],
            'message': 'Client synced to Xero successfully'
        }
    else:
        print(f"FAILED: Client {client.id} sync failed: {result.get('error')}")
        return {
            'success': False,
            'error': result.get('error'),
            'message': 'Failed to sync client to Xero'
        }

def create_xero_invoice(request, project):
    """
    Create an invoice in Xero for a project
    """
    if not project.client.xero_contact_id:
        # Sync client first if not already synced
        sync_result = sync_client_to_xero(request, project.client)
        if not sync_result['success']:
            return sync_result
    
    invoice_data = {
        "Invoices": [{
            "Type": "ACCREC",  # Accounts Receivable (customer invoice)
            "Contact": {
                "ContactID": project.client.xero_contact_id
            },
            "Date": project.created_at.strftime('%Y-%m-%d'),
            "DueDate": (project.created_at + timedelta(days=30)).strftime('%Y-%m-%d'),
            "InvoiceNumber": f"INV-{project.id}",
            "Reference": f"Project: {project.name}",
            "Status": "DRAFT",  # or "AUTHORISED" to finalize immediately
            "LineItems": [{
                "Description": f"Project: {project.name}",
                "Quantity": 1,
                "UnitAmount": float(project.approved_budget or project.estimate_cost),
                "AccountCode": "200",  # Revenue account (adjust as needed)
                "TaxType": "NONE"  # or appropriate tax code
            }]
        }]
    }
    
    result = make_xero_api_call(request, 'Invoices', method='POST', data=invoice_data)
    
    if result.get('success'):
        xero_invoice = result['data']['Invoices'][0]
        
        # Store invoice reference in project
        project.xero_invoice_id = xero_invoice['InvoiceID']
        project.xero_invoice_number = xero_invoice['InvoiceNumber']
        project.save()
        
        return {
            'success': True,
            'invoice_id': xero_invoice['InvoiceID'],
            'invoice_number': xero_invoice['InvoiceNumber'],
            'message': 'Invoice created in Xero successfully'
        }
    else:
        return {
            'success': False,
            'error': result.get('error'),
            'message': 'Failed to create invoice in Xero'
        }

def create_xero_expense(request, expense, project):
    """
    Create an expense/bill in Xero
    """
    expense_data = {
        "BankTransactions": [{
            "Type": "SPEND",
            "Contact": {
                "Name": expense.vendor_name or "General Expense"
            },
            "Date": expense.date.strftime('%Y-%m-%d'),
            "Reference": f"Project: {project.name} - {expense.description}",
            "Status": "AUTHORISED",
            "BankAccount": {
                "Code": "090"  # Use your bank account code
            },
            "LineItems": [{
                "Description": expense.description,
                "Quantity": 1,
                "UnitAmount": float(expense.amount),
                "AccountCode": get_expense_account_code(expense.category),
                "TrackingCategories": [{
                    "TrackingCategoryID": "your-project-tracking-category-id",
                    "TrackingOptionID": project.xero_tracking_option_id
                }] if hasattr(project, 'xero_tracking_option_id') else []
            }]
        }]
    }
    
    result = make_xero_api_call(request, 'BankTransactions', method='POST', data=expense_data)
    
    if result.get('success'):
        xero_transaction = result['data']['BankTransactions'][0]
        
        # Store reference in expense
        expense.xero_transaction_id = xero_transaction['BankTransactionID']
        expense.save()
        
        return {
            'success': True,
            'transaction_id': xero_transaction['BankTransactionID'],
            'message': 'Expense recorded in Xero successfully'
        }
    else:
        return {
            'success': False,
            'error': result.get('error'),
            'message': 'Failed to record expense in Xero'
        }

def get_expense_account_code(category):
    """
    Map your expense categories to Xero account codes
    """
    category_mapping = {
        'labor': '400',      # Cost of Sales
        'equipment': '410',  # Equipment Expenses
        'subcontractors': '420',  # Subcontractor Costs
        'materials': '430',  # Materials
        'other': '460'       # General Expenses
    }
    
    return category_mapping.get(category.lower(), '460')  

@method_decorator(csrf_exempt, name='dispatch')
class SyncClientToXeroView(View):
    def post(self, request, client_id):
        try:
            client = get_object_or_404(Client, id=client_id)
            
            # Use your existing sync method
            success = client.sync_to_xero(request)
            
            if success:
                return JsonResponse({
                    'success': True, 
                    'message': 'Client successfully synced to Xero!',
                    'xero_contact_id': client.xero_contact_id,
                    'last_synced': client.xero_last_sync.isoformat() if client.xero_last_sync else None
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': 'Failed to sync client to Xero. Please check your Xero connection.'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Sync error: {str(e)}'
            })