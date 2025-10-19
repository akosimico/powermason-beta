# manage_client/xero_helpers.py
import requests
from django.conf import settings
from .models import XeroConnection
from django.utils import timezone

def get_xero_connections(request):
    """Get all available Xero connections/organizations"""
    if not request.user.is_authenticated:
        return {'error': 'User not authenticated'}
    
    try:
        xero_conn = XeroConnection.objects.get(user=request.user.userprofile)
        if not xero_conn.is_valid():
            return {'error': 'Xero connection expired. Please reconnect.'}
        
        access_token = xero_conn.access_token
    except (XeroConnection.DoesNotExist, AttributeError):
        return {'error': 'Not connected to Xero'}
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    }
    
    try:
        response = requests.get('https://api.xero.com/connections', headers=headers)
        if response.status_code == 200:
            connections = response.json()
            return {'success': True, 'connections': connections}
        else:
            return {'error': f'Failed to get connections: {response.status_code}'}
    except Exception as e:
        return {'error': f'Request failed: {str(e)}'}

def make_xero_api_call(request, endpoint, method='GET', data=None, tenant_id=None):
    """
    Helper function to make authenticated Xero API calls using database-stored tokens
    """
    if not request.user.is_authenticated:
        return {'error': 'User not authenticated'}
    
    try:
        xero_conn = XeroConnection.objects.get(user=request.user.userprofile)
        if not xero_conn.is_valid():
            return {'error': 'Xero connection expired. Please reconnect.'}
        
        access_token = xero_conn.access_token
    except (XeroConnection.DoesNotExist, AttributeError):
        return {'error': 'Not connected to Xero'}
    
    # Use provided tenant_id or get stored tenant_id or fetch default
    if not tenant_id:
        tenant_id = xero_conn.tenant_id
    
    if not tenant_id:
        # Get the first available connection and store it
        connections_result = get_xero_connections(request)
        if connections_result.get('success') and connections_result['connections']:
            tenant_id = connections_result['connections'][0]['tenantId']
            xero_conn.tenant_id = tenant_id
            xero_conn.save()
        else:
            return {'error': 'No tenant ID available'}
    
    # Make the API call
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'xero-tenant-id': tenant_id,
    }
    
    if method.upper() == 'POST':
        headers['Content-Type'] = 'application/json'
    
    try:
        url = f"https://api.xero.com/api.xro/2.0/{endpoint}"
        
        if method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data)
        else:
            response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return {'success': True, 'data': response.json(), 'tenant_id': tenant_id}
        else:
            return {'error': f'API call failed: {response.status_code}', 'details': response.text}
    
    except Exception as e:
        return {'error': f'Request failed: {str(e)}'}

def has_xero_connection(user):
    """Check if user has a valid Xero connection"""
    if not user.is_authenticated:
        return False
    
    try:
        xero_conn = XeroConnection.objects.get(user=user.userprofile)
        return xero_conn.is_valid()
    except (XeroConnection.DoesNotExist, AttributeError):
        return False