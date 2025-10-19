#!/usr/bin/env python
"""
Simple test script to verify the token system fix.
This script tests the URL generation functionality.
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'powermason_capstone.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from authentication.utils.url_helpers import reverse_with_token, get_user_token, get_user_role
from authentication.models import UserProfile

User = get_user_model()

def test_url_generation():
    """Test URL generation with and without tokens"""
    
    # Create a test request factory
    factory = RequestFactory()
    
    # Test 1: Test with no user (should use session-based URLs)
    print("Test 1: No authenticated user")
    request = factory.get('/')
    request.user = User()  # Anonymous user
    request.session = {}
    
    try:
        url = reverse_with_token(request, 'project_costing_dashboard')
        print(f"✅ Session-based URL generated: {url}")
    except Exception as e:
        print(f"❌ Error generating session-based URL: {e}")
    
    # Test 2: Test with authenticated user but no token
    print("\nTest 2: Authenticated user without token")
    try:
        # Create a test user
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Create user profile
        profile = UserProfile.objects.create(user=user, role='EG')
        
        request = factory.get('/')
        request.user = user
        request.session = {}
        
        # Test token generation
        token = get_user_token(request)
        role = get_user_role(request)
        print(f"✅ Token generated: {token[:20]}...")
        print(f"✅ Role retrieved: {role}")
        
        # Test URL generation
        url = reverse_with_token(request, 'project_costing_dashboard')
        print(f"✅ URL generated: {url}")
        
        # Clean up
        user.delete()
        
    except Exception as e:
        print(f"❌ Error with authenticated user: {e}")
    
    # Test 3: Test with existing token
    print("\nTest 3: User with existing token")
    try:
        # Create a test user
        user = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        
        # Create user profile
        profile = UserProfile.objects.create(user=user, role='PM')
        
        request = factory.get('/')
        request.user = user
        request.session = {'dashboard_token': 'existing_token_123'}
        
        # Test URL generation
        url = reverse_with_token(request, 'project_costing_dashboard')
        print(f"✅ URL with existing token: {url}")
        
        # Clean up
        user.delete()
        
    except Exception as e:
        print(f"❌ Error with existing token: {e}")

if __name__ == '__main__':
    print("Testing Token System Fix...")
    print("=" * 50)
    test_url_generation()
    print("\n" + "=" * 50)
    print("Test completed!")
