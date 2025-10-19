from django.shortcuts import render
from .xero_helpers import make_xero_api_call, get_xero_connections
import requests
from django.shortcuts import redirect
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import XeroConnection
from django.contrib.auth.decorators import login_required

@login_required
def xero_connect(request):
    """Start Xero OAuth flow"""
    
    # Debug: Print the values being used
    print("=== XERO DEBUG INFO ===")
    print(f"XERO_CLIENT_ID: {settings.XERO_CLIENT_ID}")
    print(f"XERO_REDIRECT_URI: {settings.XERO_REDIRECT_URI}")
    print("======================")
    
    auth_url = (
        f"https://login.xero.com/identity/connect/authorize"
        f"?response_type=code"
        f"&client_id={settings.XERO_CLIENT_ID}"
        f"&redirect_uri={settings.XERO_REDIRECT_URI}"
        f"&scope=accounting.transactions accounting.contacts accounting.settings"
        f"&state=test123"
    )
    
    print(f"Auth URL: {auth_url}")
    return redirect(auth_url)

from django.utils import timezone
from datetime import timedelta

@csrf_exempt
def xero_callback(request):
    """Handle Xero OAuth callback"""
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    # Debug: Print what we received
    print("=== CALLBACK DEBUG ===")
    print(f"Code: {code[:20]}..." if code else "No code")
    print(f"Error: {error}")
    print(f"All GET params: {dict(request.GET)}")
    print("=====================")
    
    # Check for errors first
    if error:
        messages.error(request, f'OAuth error: {error}')
        return redirect('xero_dashboard')
    
    if not code:
        messages.error(request, 'No authorization code received')
        return redirect('xero_dashboard')
    
    # Only proceed if user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, 'You must be logged in to connect to Xero')
        return redirect('xero_dashboard')
    
    # Exchange code for access token
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': settings.XERO_REDIRECT_URI,
        'client_id': settings.XERO_CLIENT_ID,
        'client_secret': settings.XERO_CLIENT_SECRET,
    }
    
    try:
        response = requests.post(
            'https://identity.xero.com/connect/token',
            data=token_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        print(f"Token response status: {response.status_code}")
        print(f"Token response: {response.text}")
        
        if response.status_code == 200:
            tokens = response.json()
            print(f"Tokens received: {list(tokens.keys())}")
            
            # Store tokens in database model
            xero_conn, created = XeroConnection.objects.get_or_create(
                user=request.user.userprofile,
                defaults={
                    'access_token': tokens['access_token'],
                    'refresh_token': tokens.get('refresh_token', ''),
                    'expires_at': timezone.now() + timedelta(seconds=tokens.get('expires_in', 1800))
                }
            )
            if not created:
                xero_conn.access_token = tokens['access_token']
                xero_conn.refresh_token = tokens.get('refresh_token', '')
                xero_conn.expires_at = timezone.now() + timedelta(seconds=tokens.get('expires_in', 1800))
                xero_conn.save()
            
            print(f"DEBUG: Xero connection saved for user {request.user.id}")
            
            # Success - redirect to client management
            messages.success(request, 'Successfully connected to Xero!')
            return redirect('client_management')  # Redirect to where you want to use it
        else:
            # Token exchange failed
            messages.error(request, f'Token exchange failed: {response.status_code}')
            return redirect('xero_dashboard')
    
    except Exception as e:
        print(f"Error in Xero callback: {str(e)}")
        messages.error(request, f'Connection error: {str(e)}')
        return redirect('xero_dashboard')
    
def test_xero_api(request):
    """Test Xero API connection"""
    access_token = request.session.get('xero_access_token')
    
    if not access_token:
        return JsonResponse({'error': 'Not connected to Xero. Please connect first.'})
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    }
    
    try:
        # Step 1: Get connections/tenants first (no tenant-id needed for this call)
        connections_response = requests.get(
            'https://api.xero.com/connections',
            headers=headers
        )
        
        if connections_response.status_code != 200:
            return JsonResponse({
                'error': f'Failed to get connections: {connections_response.status_code}',
                'details': connections_response.text
            })
        
        connections = connections_response.json()
        
        if not connections or len(connections) == 0:
            return JsonResponse({'error': 'No Xero organizations found'})
        
        # Get the first tenant ID
        tenant_id = connections[0]['tenantId']
        
        # Store tenant_id in session for future use
        request.session['xero_tenant_id'] = tenant_id
        
        # Step 2: Now make API call with tenant-id header
        headers['xero-tenant-id'] = tenant_id  # Add the required header
        
        response = requests.get(
            'https://api.xero.com/api.xro/2.0/Organisation',
            headers=headers
        )
        
        if response.status_code == 200:
            org_data = response.json()
            return JsonResponse({
                'success': True,
                'tenant_id': tenant_id,
                'connections': connections,
                'organization': org_data
            })
        else:
            return JsonResponse({
                'error': f'API call failed: {response.status_code}',
                'details': response.text,
                'tenant_id': tenant_id
            })
    
    except Exception as e:
        return JsonResponse({'error': f'API error: {str(e)}'})

@login_required
def xero_dashboard(request):
    """Comprehensive Xero Dashboard with organization selection"""
    context = {
        'connected': False,
        'organization': None,
        'contacts': [],
        'invoices': [],
        'accounts': [],
        'bank_transactions': [],
        'financial_summary': {},
        'available_orgs': [],
        'current_org': None,
        'error': None
    }
    
    # Check if connected
    if not request.session.get('xero_access_token'):
        return render(request, 'xero_dashboard.html', context)
    
    context['connected'] = True
    
    # Get all available organizations
    connections_result = get_xero_connections(request)
    if connections_result.get('success'):
        context['available_orgs'] = connections_result['connections']
        
        # Set current organization
        current_tenant_id = request.session.get('xero_selected_tenant_id') or request.session.get('xero_tenant_id')
        if current_tenant_id:
            context['current_org'] = next(
                (org for org in context['available_orgs'] if org['tenantId'] == current_tenant_id),
                context['available_orgs'][0] if context['available_orgs'] else None
            )
        elif context['available_orgs']:
            # Set first org as default
            context['current_org'] = context['available_orgs'][0]
            request.session['xero_selected_tenant_id'] = context['current_org']['tenantId']
    else:
        context['error'] = connections_result.get('error')
        return render(request, 'xero_dashboard.html', context)
    
    if not context['current_org']:
        context['error'] = 'No organizations available'
        return render(request, 'xero_dashboard.html', context)
    
    current_tenant_id = context['current_org']['tenantId']
    
    # Get Organization Info
    org_result = make_xero_api_call(request, 'Organisation', tenant_id=current_tenant_id)
    if org_result.get('success'):
        context['organization'] = org_result['data']['Organisations'][0]
    else:
        context['error'] = org_result.get('error')
        return render(request, 'xero_dashboard.html', context)
    
    # Get other data using the selected tenant_id
    # Get Contacts (Clients)
    contacts_result = make_xero_api_call(request, 'Contacts', tenant_id=current_tenant_id)
    if contacts_result.get('success'):
        contacts = contacts_result['data']['Contacts']
        context['contacts'] = sorted(
            [c for c in contacts if c.get('ContactStatus') == 'ACTIVE'],
            key=lambda x: x.get('Name', '')
        )[:10]
    
    # Get Recent Invoices
    invoices_result = make_xero_api_call(request, 'Invoices?order=Date DESC', tenant_id=current_tenant_id)
    if invoices_result.get('success'):
        context['invoices'] = invoices_result['data']['Invoices'][:5]
    
    # Get Chart of Accounts
    accounts_result = make_xero_api_call(request, 'Accounts', tenant_id=current_tenant_id)
    if accounts_result.get('success'):
        all_accounts = accounts_result['data']['Accounts']
        context['accounts'] = {
            'revenue': [acc for acc in all_accounts if acc.get('Type') == 'REVENUE'],
            'expense': [acc for acc in all_accounts if acc.get('Type') == 'EXPENSE'],
            'asset': [acc for acc in all_accounts if acc.get('Type') == 'CURRENT' and 'ASSET' in acc.get('Class', '')],
        }
    
    # Get Recent Bank Transactions
    bank_result = make_xero_api_call(request, 'BankTransactions?order=Date DESC', tenant_id=current_tenant_id)
    if bank_result.get('success'):
        context['bank_transactions'] = bank_result['data']['BankTransactions'][:5]
    
    # Calculate Financial Summary
    context['financial_summary'] = calculate_financial_summary(context)
    
    return render(request, 'xero_dashboard.html', context)

def calculate_financial_summary(context):
    """Calculate key financial metrics"""
    summary = {
        'total_contacts': len(context.get('contacts', [])),
        'total_invoices': 0,
        'total_revenue': 0,
        'outstanding_amount': 0,
        'recent_transactions': len(context.get('bank_transactions', []))
    }
    
    # Calculate invoice metrics
    for invoice in context.get('invoices', []):
        summary['total_invoices'] += 1
        if invoice.get('Total'):
            summary['total_revenue'] += float(invoice.get('Total', 0))
        if invoice.get('Status') == 'AUTHORISED' and invoice.get('AmountDue'):
            summary['outstanding_amount'] += float(invoice.get('AmountDue', 0))
    
    return summary
    
# manage_client/views.py (add these views)
def switch_xero_organization(request):
    """Switch to a different Xero organization"""
    if request.method == 'POST':
        tenant_id = request.POST.get('tenant_id')
        if tenant_id:
            request.session['xero_selected_tenant_id'] = tenant_id
            return JsonResponse({'success': True, 'message': 'Organization switched successfully'})
        return JsonResponse({'error': 'No tenant ID provided'})
    
    # GET request - show available organizations
    connections_result = get_xero_connections(request)
    
    if not connections_result.get('success'):
        return JsonResponse({'error': connections_result.get('error')})
    
    return JsonResponse({
        'success': True,
        'connections': connections_result['connections'],
        'current_tenant_id': request.session.get('xero_selected_tenant_id') or request.session.get('xero_tenant_id')
    })
