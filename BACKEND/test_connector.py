#!/usr/bin/env python3
"""
Script de test pour le connecteur communautaire Looker Studio basé sur Client
"""
import os
import sys
import json
import django
import logging
import datetime
from pathlib import Path

# Add the project directory to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
try:
    django.setup()
    print("✅ Django environment initialized.")
except Exception as e:
    print(f"❌ Failed to initialize Django: {e}")
    sys.exit(1)

import requests
from django.contrib.auth import get_user_model
from play_reports.models import Client, Tenant, Abonnement, TypeAbonnement

# Configuration
API_BASE_URL = 'http://localhost:8000'  # Base URL for the API

LOOKER_PREFIX = '/api/looker-community'
# Updated to use the correct authentication endpoint
AUTH_URL = f"{API_BASE_URL}/client/login/"
VERIFY_SUBSCRIPTION_URL = f"{API_BASE_URL}{LOOKER_PREFIX}/subscription/verify"
METADATA_URL = f"{API_BASE_URL}{LOOKER_PREFIX}/datasources/metadata"
SCHEMA_URL = f"{API_BASE_URL}{LOOKER_PREFIX}/schema"
DATA_URL = f"{API_BASE_URL}{LOOKER_PREFIX}/data"
HEALTH_URL = f"{API_BASE_URL}{LOOKER_PREFIX}/health"

# Test configuration
TEST_CONFIG = {
    'test_user': {
        'email': 'imed@clubprivileges.app',
        'password': 'imed2025*',
        'expected_plan': 'ENTERPRISE',
        'expected_sources': 4,
        'test_data': {
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'package_name': 'com.example.app',
            'test_limit': 5
        }
    },
    'tables_to_test': [
        'google_play_installs_overview',
        'google_play_ratings_overview',
        'google_play_crashes_overview',
        'google_play_revenue'
    ]
}

# Console colors and formatting
class Colors:
    HEADER = '\033[95m'; BLUE = '\033[94m'; CYAN = '\033[96m'
    GREEN = '\033[92m'; YELLOW = '\033[93m'; RED = '\033[91m'
    BOLD = '\033[1m'; UNDERLINE = '\033[4m'; RESET = '\033[0m'
    
    @classmethod
    def colorize(cls, text, color):
        return f"{color}{text}{cls.RESET}"
    
    @classmethod
    def print_section(cls, title):
        border = "=" * 60
        print(f"\n{cls.HEADER}{cls.BOLD}{border}")
        print(f"{title.upper():^60}")
        print(f"{border}{cls.RESET}\n")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.RESET}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")

def print_debug(message, data=None):
    if os.environ.get('DEBUG', 'false').lower() == 'true':
        print(f"{Colors.CYAN}🐛 {message}")
        if data is not None:
            print(f"{Colors.CYAN}   {json.dumps(data, indent=2, default=str)}{Colors.RESET}")

def print_header(message):
    Colors.print_section(f"🚀 {message}")

def print_test_result(test_name, success, message=None):
    if success:
        print(f"{Colors.GREEN}✓ {test_name}: PASSED{Colors.RESET}")
    else:
        print(f"{Colors.RED}✗ {test_name}: FAILED - {message or 'Unknown error'}{Colors.RESET}")
    return success

# ------------------------------
# API Request Helper
# ------------------------------
def make_api_request(method, url, headers=None, params=None, json_data=None, auth_token=None):
    """Helper function to make API requests with error handling."""
    try:
        headers = headers or {}
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
            
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_data,
            timeout=30
        )
        
        print_debug(f"API Request: {method} {url}", {
            'status_code': response.status_code,
            'headers': dict(response.request.headers),
            'params': params,
            'request_body': json_data,
            'response': response.text[:500] + ('...' if len(response.text) > 500 else '')
        })
        
        return response
        
    except requests.exceptions.RequestException as e:
        print_error(f"API Request failed: {str(e)}")
        return None

# ------------------------------
# Health check
# ------------------------------
def test_health_check():
    """Test if the API health check endpoint is responding."""
    print_header("Testing Health Check")
    response = make_api_request('GET', HEALTH_URL)
    
    if not response:
        return False
        
    if response.status_code == 200:
        data = response.json()
        print_success(f"Health check passed: {data}")
        return True
    else:
        print_error(f"Health check failed with status {response.status_code}")
        print_info(f"Response: {response.text}")
        return False

# ------------------------------
# Ensure test data exists
# ------------------------------
def ensure_test_data_exists():
    """Ensure test client, tenant, and subscription exist."""
    print_header("Verifying Test Data")
    
    try:
        User = get_user_model()
        test_data = TEST_CONFIG['test_user']
        
        # Check if user already exists
        user = User.objects.filter(email=test_data['email']).first()
        
        if user is None:
            print(f"Creating test user: {test_data['email']}")
            # Create user with email as username if needed
            user = User.objects.create_user(
                email=test_data['email'],
                password=test_data['password'],
                first_name='Test',
                last_name='User',
                is_active=True
            )
            print(f"Created user: {user}")
        else:
            print(f"Using existing user: {user}")
            # Ensure password is set correctly
            if not user.check_password(test_data['password']):
                user.set_password(test_data['password'])
                user.save()
        
        # Vérifier si le client existe déjà
        client = Client.objects.filter(user=user).first()
        
        if client:
            # Utiliser le tenant existant
            tenant = client.tenant
            subscription = client.abonnement
            print(f"Using existing client with tenant: {tenant.name}")
        else:
            # Créer un nouveau tenant uniquement si le client n'existe pas
            tenant, _ = Tenant.objects.get_or_create(
                name='Test Tenant',
                defaults={'is_active': True}
            )
            
            # Créer un nouvel abonnement
            from django.utils import timezone
            future_date = timezone.now() + timezone.timedelta(days=365)
            
            subscription, _ = Abonnement.objects.get_or_create(
                type_abonnement=TypeAbonnement.PRO,
                defaults={
                    'is_active': True,
                    'date_fin': future_date
                }
            )
            
            # Créer le client
            client = Client.objects.create(
                user=user,
                first_name='Test',
                last_name='Client',
                email=test_data['email'],
                tenant=tenant,
                abonnement=subscription,
                status='active'
            )
            print(f"Created new client with tenant: {tenant.name}")
        
        # Vérifier que l'abonnement a une date de fin valide
        if not hasattr(subscription, 'date_fin') or not subscription.date_fin:
            future_date = timezone.now() + timezone.timedelta(days=365)
            subscription.date_fin = future_date
            subscription.save()
            print("Updated subscription with future end date")
        
        print_success(f"Test client configured: {client.email}")
        print_info(f"Tenant: {tenant.name} (Active: {tenant.is_active})")
        print_info(f"Subscription: {subscription.get_type_abonnement_display()} (Active: {subscription.is_active})")
        
        return True
        
    except Exception as e:
        print_error(f"Error setting up test data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
# ------------------------------
# Authentication
# ------------------------------
def test_authentication():
    """Test user authentication and JWT token retrieval."""
    print_header("Testing Authentication")
    
    test_data = TEST_CONFIG['test_user']
    email = test_data['email']
    password = test_data['password']
    
    # Make authentication request
    print_info(f"Authenticating user: {email}")
    
    try:
        # Make a direct request to the login endpoint
        response = requests.post(
            AUTH_URL,
            data={
                'email': email,
                'password': password
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            }
        )
        
        if response.status_code == 200:
            response_data = response.json()
            if 'access' in response_data:
                token = response_data['access']
                print_success(f"Authentication successful for {email}")
                print_info(f"Token: {token[:20]}...")
                return token
            else:
                print_error(f"No access token in response: {response_data}")
        else:
            error_msg = response.text
            print_error(f"Authentication failed (HTTP {response.status_code}): {error_msg}")
    except Exception as e:
        print_error(f"Error during authentication: {str(e)}")
    
    return None
    
    return None

# ------------------------------
# Subscription verification
# ------------------------------
def test_subscription_verification(token):
    """Verify the user's subscription status."""
    print_header("Testing Subscription Verification")
    
    response = make_api_request(
        'GET',
        VERIFY_SUBSCRIPTION_URL,
        auth_token=token
    )
    
    if not response:
        return None
    
    data = response.json()
    print_debug("Subscription verification response:", data)
    
    if response.status_code == 200 and data.get('is_active', False):
        plan = data.get('subscription_plan', 'unknown')
        status = data.get('subscription_status', 'unknown')
        expiry = data.get('expiry_date', 'No expiry date')
        print_success(f"Subscription verified - Plan: {plan}, Status: {status}, Expiry: {expiry}")
        return plan
    else:
        error_msg = data.get('message', 'No error message')
        status = data.get('subscription_status', 'unknown')
        print_error(f"Subscription verification failed - Status: {status}, Error: {error_msg}")
        
    return None

# ------------------------------
# Metadata
# ------------------------------
def test_metadata(token, expected_sources):
    print_header("Testing Metadata Endpoint")
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(METADATA_URL, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                sources = data.get('data', {}).get('sources', [])
                source_count = len(sources)
                if source_count >= expected_sources:
                    print_success(f"Found {source_count} data sources (expected at least {expected_sources})")
                else:
                    print_warning(f"Found only {source_count} sources (expected at least {expected_sources})")
                return sources
            else:
                print_error(f"Metadata request failed: {data.get('message', 'No message')}")
        else:
            print_error(f"Metadata request failed with status {response.status_code}")
            print_info(f"Response: {response.text}")
    except Exception as e:
        print_error(f"Metadata request error: {str(e)}")
    return []

# ------------------------------
# Schema
# ------------------------------
def test_schema(token, table_name):
    """Test the schema endpoint for a specific table."""
    print_header(f"Testing Schema for {table_name}")
    
    url = f"{SCHEMA_URL}/{table_name}"
    print_debug(f"Making request to: {url}")
    
    response = make_api_request(
        'GET',
        url,
        auth_token=token,
        headers={'Content-Type': 'application/json'}
    )
    
    if not response:
        print_error("No response received from server")
        return False
    
    try:
        data = response.json()
        print_debug(f"Schema response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200:
            # Check for error response
            if isinstance(data, dict) and 'success' in data and not data['success']:
                print_error(f"Schema request failed: {data.get('message', 'Unknown error')}")
                return False
            
            # Extract schema from the response
            if isinstance(data, dict) and 'data' in data and 'schema' in data['data']:
                schema = data['data']['schema']
                print_debug(f"Extracted schema from data.schema: {len(schema)} fields")
            elif isinstance(data, dict) and 'data' in data and 'fields' in data['data']:
                schema = data['data']['fields']
                print_debug(f"Extracted schema from data.fields: {len(schema)} fields")
            elif isinstance(data, dict) and 'fields' in data:
                schema = data['fields']
                print_debug(f"Extracted schema from fields: {len(schema)} fields")
            else:
                schema = data if isinstance(data, list) else []
                print_debug(f"Using raw response as schema: {len(schema)} items")
            
            if not isinstance(schema, list):
                print_error(f"Unexpected schema format: {type(schema).__name__}")
                print_debug(f"Schema content: {schema}")
                return False
                
            field_count = len(schema)
            
            if field_count > 0:
                print_success(f"Found {field_count} fields in {table_name} schema")
                
                # Safely format field information
                field_info = []
                for field in schema[:5]:  # Only show first 5 fields to avoid cluttering output
                    if isinstance(field, dict):
                        name = field.get('name', field.get('id', 'unknown'))
                        data_type = field.get('type', field.get('dataType', 'unknown'))
                        label = field.get('label', field.get('description', ''))
                        field_info.append(f"{name} ({data_type}): {label}")
                    else:
                        field_info.append(str(field))
                
                if field_count > 5:
                    field_info.append(f"... and {field_count - 5} more fields")
                
                print_info("Sample fields:")
                for field in field_info:
                    print(f"  - {field}")
                    
                return True
            else:
                print_error(f"No fields found in {table_name} schema")
                print_debug(f"Response data: {data}")
                return False
        else:
            error_msg = data.get('message', f"HTTP {response.status_code}")
            print_error(f"Schema request failed: {error_msg}")
            print_debug(f"Full response: {data}")
            return False
    except Exception as e:
        print_error(f"Error processing schema response: {str(e)}")
        if 'response' in locals():
            print_debug(f"Response content: {response.text}")
        import traceback
        traceback.print_exc()
        return False
    
    return False, []

# ------------------------------
# Data
# ------------------------------
def test_data(token: str, table_name: str, limit: int = 5) -> bool:
    """Test data retrieval for a specific table.
    
    Args:
        token: JWT authentication token
        table_name: Name of the table to test
        limit: Maximum number of rows to fetch
        
    Returns:
        bool: True if data was successfully retrieved, False otherwise
    """
    print_header(f"Testing Data Retrieval for {table_name}")
    
    # Build request parameters based on table type
    params = {'limit': min(limit, 10)}  # Cap limit for testing
    
    # Add date range for time-series data
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=30)  # Last 30 days
    
    if 'date' in table_name.lower() or 'overview' in table_name.lower():
        params.update({
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
    
    # Add package name for Google Play data
    if 'google_play' in table_name.lower():
        params['package_name'] = 'com.example.app'  # Replace with actual test package
    
    # Make the API request
    response = make_api_request(
        'GET',
        f"{DATA_URL}/{table_name}",
        params=params,
        auth_token=token
    )
    if not response:
        return False
    
    try:
        data = response.json()
        print_debug(f"Data response: {json.dumps(data, indent=2, default=str)}")
        
        if response.status_code == 200 and data.get('success', False):
            # Handle different possible response formats
            if isinstance(data, dict) and 'data' in data:
                rows = data['data']
                if not isinstance(rows, list):
                    rows = [rows]  # Convert single object to list
            elif isinstance(data, list):
                rows = data
            else:
                rows = []
            
            row_count = len(rows)
            
            if row_count > 0:
                print_success(f"Retrieved {row_count} rows from {table_name}")
                
                # Print column names from first row if available
                if rows and isinstance(rows[0], dict):
                    columns = list(rows[0].keys())
                    print_info(f"Columns: {', '.join(columns)}")
                    
                    # Print sample data (limited to 3 rows)
                    print_info("Sample data:")
                    for i, row in enumerate(rows[:3], 1):
                        # Format row values for display
                        row_display = []
                        for k, v in row.items():
                            if v is None:
                                v = 'NULL'
                            elif isinstance(v, str):
                                if len(v) > 30:
                                    v = v[:27] + '...'
                            elif isinstance(v, (dict, list)):
                                v = json.dumps(v)[:30] + '...' if len(json.dumps(v)) > 30 else json.dumps(v)
                            row_display.append(f"{k}: {v}")
                        print_info(f"  Row {i}: {', '.join(row_display)}")
                else:
                    print_info(f"Data format: {type(rows[0]).__name__}")
                    print_info(f"First row: {str(rows[0])}")
                
                return True
            else:
                print_warning(f"No data returned for {table_name}")
                print_debug(f"Response data: {data}")
                return False
        else:
            error_msg = data.get('message', f'HTTP {response.status_code}: No error message')
            print_error(f"Data request failed: {error_msg}")
            return False
            
    except json.JSONDecodeError as e:
        print_error(f"Failed to parse JSON response: {str(e)}")
        print_debug(f"Raw response: {response.text}")
        return False
    except Exception as e:
        print_error(f"Error processing data response: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# ------------------------------
# Main Test Runner
# ------------------------------
def run_tests():
    """Run all tests and return the results."""
    print("Initializing test runner...")
    print_header("Starting Looker Community Connector Tests")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    
    # Initialize test results structure
    test_results = {
        'core': {
            'health_check': False,
            'test_data': False,
            'authentication': False,
            'subscription': False
        },
        'tables': {table_name: {'schema': False, 'data': False} 
                  for table_name in TEST_CONFIG['tables_to_test']}
    }
    print("Test results structure initialized")
    
    # Core Tests
    print_header("Running Core Tests")
    
    try:
        # 1. Health Check
        test_results['core']['health_check'] = test_health_check()
        
        # 2. Test Data Setup
        test_results['core']['test_data'] = ensure_test_data_exists()
        if not test_results['core']['test_data']:
            print_error("Cannot continue with tests: Test data setup failed")
            return test_results
        
        # 3. Authentication
        token = test_authentication()
        test_results['core']['authentication'] = token is not None
        
        if not test_results['core']['authentication']:
            print_error("Cannot continue with tests: Authentication failed")
            return test_results
        
        # 4. Subscription Verification
        test_results['core']['subscription'] = test_subscription_verification(token)
        
        # Table Tests
        if test_results['core']['authentication'] and token:
            print_header("Running Table Tests")
            
            for table_name in TEST_CONFIG['tables_to_test']:
                print(f"\n{'='*60}")
                print(f"Testing Table: {table_name}".center(60))
                print(f"{'='*60}")
                
                # Test Schema
                schema_result = test_schema(token, table_name)
                test_results['tables'][table_name]['schema'] = schema_result
                
                # Test Data if schema test passed
                if schema_result:
                    data_result = test_data(
                        token, 
                        table_name, 
                        limit=TEST_CONFIG['test_user']['test_data']['test_limit']
                    )
                    test_results['tables'][table_name]['data'] = data_result
    
    except Exception as e:
        print_error(f"Error during test execution: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return test_results

def print_test_summary(test_results):
    """Print a summary of test results."""
    if not test_results or not isinstance(test_results, dict):
        print_error("Invalid test results format")
        return False
    
    print_header("Test Summary")
    
    # Core Tests Summary
    print("\nCore Tests:")
    core_passed = True
    for test_name, result in test_results.get('core', {}).items():
        if isinstance(result, bool):
            status = "PASSED" if result else "FAILED"
            color = Colors.GREEN if result else Colors.RED
            print(f"  {test_name.replace('_', ' ').title()}: {Colors.colorize(status, color)}")
            if not result:
                core_passed = False
    
    # Table Tests Summary
    tables_passed = True
    if test_results.get('tables'):
        print("\nTable Tests:")
        for table_name, results in test_results['tables'].items():
            if not isinstance(results, dict):
                continue
                
            schema_ok = results.get('schema', False)
            data_ok = results.get('data', False)
            
            schema_status = "✓" if schema_ok else "✗"
            data_status = "✓" if data_ok else "✗"
            
            if not schema_ok or not data_ok:
                tables_passed = False
                
            print(f"  {table_name}: Schema: {schema_status} | Data: {data_status}")
    
    # Overall Status
    all_passed = core_passed and tables_passed
    
    status = "COMPLETED SUCCESSFULLY" if all_passed else "COMPLETED WITH ISSUES"
    color = Colors.GREEN if all_passed else Colors.YELLOW
    
    print(f"\n{'-'*60}")
    print(Colors.colorize(f"TESTING {status}".center(60, ' '), color))
    print(f"{'-'*60}")
    
    return all_passed

def main():
    """Main entry point for the test connector."""
    print("Starting test connector...")
    try:
        print("1. Running tests...")
        test_results = run_tests()
        print("2. Tests completed, printing summary...")
        
        if test_results:
            print("3. Test results structure:", json.dumps(test_results, indent=2, default=str))
            all_passed = print_test_summary(test_results)
            print(f"4. All tests {'PASSED' if all_passed else 'FAILED'}")
            sys.exit(0 if all_passed else 1)
        else:
            print_error("No test results returned")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nTest execution cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error in main: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest execution cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print_error(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\nTesting completed!")
