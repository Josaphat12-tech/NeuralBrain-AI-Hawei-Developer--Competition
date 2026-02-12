#!/usr/bin/env python3
"""
HUAWEI CLOUD CREDENTIAL CONFIGURATION
======================================

This script helps you configure your Huawei Cloud credentials from the $100 coupon.

Usage:
    python3 configure_credentials.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv, dotenv_values

# Color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{CYAN}{'='*70}{RESET}")
    print(f"{CYAN}{text.center(70)}{RESET}")
    print(f"{CYAN}{'='*70}{RESET}\n")

def print_section(text):
    print(f"\n{BLUE}► {text}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")

def print_info(text):
    print(f"{CYAN}ℹ{RESET} {text}")

def print_warning(text):
    print(f"{YELLOW}⚠{RESET} {text}")

def print_error(text):
    print(f"{RED}✗{RESET} {text}")

def load_env():
    """Load current .env file"""
    env_path = Path('.env')
    if env_path.exists():
        load_dotenv(env_path)
        return dotenv_values(env_path)
    return {}

def update_env(key, value):
    """Update .env file with new key-value pair"""
    env_path = Path('.env')
    
    if not env_path.exists():
        env_path.write_text(f"{key}={value}\n")
        return
    
    content = env_path.read_text()
    lines = content.split('\n')
    
    found = False
    new_lines = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)
    
    if not found:
        new_lines.append(f"{key}={value}")
    
    env_path.write_text('\n'.join(new_lines))

def get_user_input(prompt, mask=False):
    """Get input from user, optionally masking it"""
    if mask:
        import getpass
        return getpass.getpass(prompt)
    else:
        return input(prompt)

def validate_api_key(key):
    """Validate API key format"""
    if not key or len(key) < 10:
        return False, "API key too short (minimum 10 characters)"
    return True, "Valid"

def validate_project_id(project_id):
    """Validate project ID format"""
    if not project_id or len(project_id) < 5:
        return False, "Project ID too short (minimum 5 characters)"
    # Huawei project IDs are usually UUIDs or project codes
    if ' ' in project_id:
        return False, "Project ID contains spaces"
    return True, "Valid"

def main():
    print_header("HUAWEI CLOUD CREDENTIAL CONFIGURATION")
    
    os.chdir(Path(__file__).parent)
    
    print_info("This tool will help you configure Huawei Cloud credentials from your $100 coupon.")
    print_info("Your credentials will be saved securely in .env file.\n")
    
    # Load current .env
    current_env = load_env()
    
    print_section("Step 1: Huawei Cloud API Key")
    
    print("Your API Key should come from your Huawei Cloud console:")
    print("  1. Login to https://console.huaweicloud.com")
    print("  2. Go to: My Credentials → API Credentials")
    print("  3. Copy your Access Key (AK)")
    print()
    
    current_api_key = current_env.get('HUAWEI_API_KEY', '')
    if current_api_key and not current_api_key.startswith('${'):
        print_info(f"Current API Key: {current_api_key[:6]}{'*'*20}")
        use_current = input("Use current API Key? (y/n): ").lower() == 'y'
        if use_current:
            api_key = current_api_key
        else:
            api_key = get_user_input("Enter your Huawei Cloud API Key (Access Key): ", mask=True)
    else:
        api_key = get_user_input("Enter your Huawei Cloud API Key (Access Key): ", mask=True)
    
    is_valid, msg = validate_api_key(api_key)
    if not is_valid:
        print_error(msg)
        return 1
    
    print_success("API Key validated")
    update_env('HUAWEI_API_KEY', api_key)
    print_success("API Key saved to .env")
    
    # Step 2: Project ID
    print_section("Step 2: Huawei Cloud Project ID")
    
    print("Your Project ID should come from your Huawei Cloud console:")
    print("  1. Login to https://console.huaweicloud.com")
    print("  2. Go to: My Credentials → API Credentials")
    print("  3. Look for IAM Project ID or Project Name")
    print("  4. Or check: Manage → Tenants and Projects → Project ID")
    print()
    
    current_project_id = current_env.get('HUAWEI_MODELARTS_PROJECT_ID', '')
    if current_project_id and not current_project_id.startswith('${'):
        print_info(f"Current Project ID: {current_project_id}")
        use_current = input("Use current Project ID? (y/n): ").lower() == 'y'
        if use_current:
            project_id = current_project_id
        else:
            project_id = get_user_input("Enter your Huawei Cloud Project ID: ")
    else:
        project_id = get_user_input("Enter your Huawei Cloud Project ID: ")
    
    is_valid, msg = validate_project_id(project_id)
    if not is_valid:
        print_error(msg)
        return 1
    
    print_success("Project ID validated")
    update_env('HUAWEI_MODELARTS_PROJECT_ID', project_id)
    print_success("Project ID saved to .env")
    
    # Step 3: Enable cloud services
    print_section("Step 3: Enable Huawei Cloud Services")
    
    enable_cloud = input("Enable Huawei Cloud services? (y/n): ").lower() == 'y'
    if enable_cloud:
        update_env('HUAWEI_CLOUD_ENABLED', 'true')
        print_success("Huawei Cloud services ENABLED")
    else:
        update_env('HUAWEI_CLOUD_ENABLED', 'false')
        print_warning("Huawei Cloud services DISABLED (using fallback only)")
    
    # Summary
    print_section("Configuration Summary")
    
    print_success("✓ API Key configured")
    print_success("✓ Project ID configured")
    print_success("✓ Cloud services status configured")
    
    print_section("Verification")
    
    # Reload and verify
    load_dotenv(Path('.env'))
    
    api_key_set = os.getenv('HUAWEI_API_KEY') and not os.getenv('HUAWEI_API_KEY').startswith('${')
    project_id_set = os.getenv('HUAWEI_MODELARTS_PROJECT_ID') and not os.getenv('HUAWEI_MODELARTS_PROJECT_ID').startswith('${')
    cloud_enabled = os.getenv('HUAWEI_CLOUD_ENABLED', 'false').lower() == 'true'
    
    if api_key_set:
        masked_key = os.getenv('HUAWEI_API_KEY')[:6] + '*'*20
        print_success(f"API Key: {masked_key}")
    else:
        print_error("API Key not set")
    
    if project_id_set:
        print_success(f"Project ID: {os.getenv('HUAWEI_MODELARTS_PROJECT_ID')}")
    else:
        print_error("Project ID not set")
    
    if cloud_enabled:
        print_success("Huawei Cloud services: ENABLED")
    else:
        print_info("Huawei Cloud services: DISABLED")
    
    print_section("Next Steps")
    
    print("1. Review configuration:")
    print("   cat .env | grep HUAWEI")
    print()
    
    print("2. Run the deployment checklist:")
    print("   python3 DEPLOYMENT_CHECKLIST.py")
    print()
    
    print("3. Start the Flask application:")
    print("   python3 app.py")
    print()
    
    print("4. Test the endpoints:")
    print("   curl http://localhost:5000/")
    print()
    
    print_info("Credentials are now configured!")
    print_info("The system will use real Huawei Cloud services when available")
    print_info("and automatically fallback to local implementations if needed.")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_error("\nConfiguration cancelled")
        sys.exit(1)
    except Exception as e:
        print_error(f"Configuration error: {e}")
        sys.exit(1)
