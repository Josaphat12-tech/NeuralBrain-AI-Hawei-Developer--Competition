"""
DEPLOYMENT CHECKLIST FOR HUAWEI CLOUD INTEGRATION
==================================================

This checklist ensures successful deployment of Huawei Cloud AI services
with your $100 coupon. Follow each step before marking complete.

Run this from the project root:
    python3 DEPLOYMENT_CHECKLIST.py
"""

import os
import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_section(text):
    print(f"\n{BLUE}► {text}{RESET}")

def print_task(number, text, completed=False):
    status = f"{GREEN}✓{RESET}" if completed else f"{YELLOW}○{RESET}"
    print(f"  {status} {number}. {text}")

def print_success(text):
    print(f"  {GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"  {RED}✗ {text}{RESET}")

def print_warning(text):
    print(f"  {YELLOW}⚠ {text}{RESET}")

def print_info(text):
    print(f"  {BLUE}ℹ {text}{RESET}")

def check_file_exists(path, name):
    if Path(path).exists():
        print_success(f"{name} exists")
        return True
    else:
        print_error(f"{name} not found at {path}")
        return False

def check_env_variable(var_name, required=True, placeholder=None):
    value = os.getenv(var_name)
    if placeholder and value == placeholder:
        print_warning(f"{var_name} still has placeholder value")
        return False
    if required and not value:
        print_error(f"{var_name} not set in .env")
        return False
    if value and value != placeholder:
        # Mask sensitive values
        if 'KEY' in var_name or 'TOKEN' in var_name:
            masked = value[:4] + '*' * max(0, len(value) - 8) + value[-4:]
        else:
            masked = value
        print_success(f"{var_name} = {masked}")
        return True
    return True

def main():
    print_header("HUAWEI CLOUD AI SERVICES DEPLOYMENT CHECKLIST")
    
    os.chdir(Path(__file__).parent)
    
    # Phase 1: Environment Setup
    print_section("PHASE 1: Environment Setup")
    phase1_pass = True
    
    print_task(1, "Python 3.12+ available")
    result = os.system("python3 --version > /dev/null 2>&1")
    if result == 0:
        print_success("Python version: OK")
    else:
        print_error("Python 3 not found")
        phase1_pass = False
    
    print_task(2, "Virtual environment active")
    if sys.prefix != sys.base_prefix:
        print_success("Virtual environment is active")
    else:
        print_warning("Virtual environment may not be active")
        print_info("Activate with: source venv/bin/activate")
    
    print_task(3, "Required packages installed")
    try:
        import flask
        import sqlalchemy
        import pytest
        print_success("Flask, SQLAlchemy, pytest installed")
    except ImportError as e:
        print_error(f"Missing package: {e}")
        phase1_pass = False
    
    # Phase 2: Project Structure
    print_section("PHASE 2: Project Structure")
    phase2_pass = True
    
    files_to_check = [
        ("ai_services/__init__.py", "AI Services module"),
        ("ai_services/config.py", "Configuration manager"),
        ("ai_services/inference_adapter.py", "Health metrics adapter"),
        ("ai_services/risk_scoring_engine.py", "Risk scoring engine"),
        ("ai_services/forecast_engine.py", "Forecast engine"),
        ("tests/test_config.py", "Configuration tests"),
        ("tests/test_adapters.py", "Adapter tests"),
        ("tests/test_integration.py", "Integration tests"),
        ("tests/test_performance.py", "Performance tests"),
        (".env", "Environment configuration"),
        ("app.py", "Flask application"),
    ]
    
    for file_path, description in files_to_check:
        full_path = Path(file_path)
        if check_file_exists(full_path, f"{description} ({file_path})"):
            pass
        else:
            phase2_pass = False
    
    # Phase 3: Environment Configuration
    print_section("PHASE 3: Environment Configuration")
    phase3_pass = True
    
    print_task(1, "Load .env file")
    if Path('.env').exists():
        from dotenv import load_dotenv
        load_dotenv()
        print_success(".env loaded")
    else:
        print_error(".env file not found")
        phase3_pass = False
    
    print_task(2, "Basic Flask configuration")
    if check_env_variable("FLASK_ENV", required=False):
        pass
    else:
        print_warning("FLASK_ENV not set (using default)")
    
    print_task(3, "Database configuration")
    if check_env_variable("SQLALCHEMY_DATABASE_URI", required=False):
        pass
    else:
        print_info("Using default SQLite database")
    
    print_task(4, "Huawei Cloud enabled")
    if check_env_variable("HUAWEI_CLOUD_ENABLED", required=False):
        enabled = os.getenv("HUAWEI_CLOUD_ENABLED", "false").lower() == "true"
        if enabled:
            print_success("Huawei Cloud services ENABLED")
        else:
            print_warning("Huawei Cloud services DISABLED (using fallback only)")
    
    # Phase 4: Huawei Cloud Credentials
    print_section("PHASE 4: Huawei Cloud Credentials")
    phase4_pass = True
    
    print_task(1, "API Key configured", os.getenv("HUAWEI_API_KEY") and os.getenv("HUAWEI_API_KEY") != "${HUAWEI_CLOUD_API_KEY}")
    if os.getenv("HUAWEI_API_KEY"):
        if os.getenv("HUAWEI_API_KEY").startswith("${"):
            print_warning("HUAWEI_API_KEY still has placeholder value")
            print_info("Update with: export HUAWEI_API_KEY='your_actual_key'")
            phase4_pass = False
        else:
            print_success("HUAWEI_API_KEY configured")
    else:
        print_error("HUAWEI_API_KEY not set")
        phase4_pass = False
    
    print_task(2, "Project ID configured", os.getenv("HUAWEI_MODELARTS_PROJECT_ID") and os.getenv("HUAWEI_MODELARTS_PROJECT_ID") != "${HUAWEI_PROJECT_ID}")
    if os.getenv("HUAWEI_MODELARTS_PROJECT_ID"):
        if os.getenv("HUAWEI_MODELARTS_PROJECT_ID").startswith("${"):
            print_warning("HUAWEI_MODELARTS_PROJECT_ID still has placeholder value")
            print_info("Update with: export HUAWEI_MODELARTS_PROJECT_ID='your_actual_id'")
            phase4_pass = False
        else:
            print_success("HUAWEI_MODELARTS_PROJECT_ID configured")
    else:
        print_error("HUAWEI_MODELARTS_PROJECT_ID not set")
        phase4_pass = False
    
    print_task(3, "Cloud endpoints configured")
    endpoints_ok = (
        os.getenv("HUAWEI_MODELARTS_ENDPOINT") and 
        os.getenv("HUAWEI_TIMESERIES_ENDPOINT")
    )
    if endpoints_ok:
        print_success("Huawei Cloud endpoints configured")
    else:
        print_error("Missing cloud endpoints")
        phase4_pass = False
    
    # Phase 5: Test Suite
    print_section("PHASE 5: Test Suite Verification")
    phase5_pass = True
    
    print_task(1, "Run configuration tests")
    result = os.system("python3 -m pytest tests/test_config.py -v --tb=short > /dev/null 2>&1")
    if result == 0:
        print_success("Configuration tests passed")
    else:
        print_error("Configuration tests failed")
        phase5_pass = False
    
    print_task(2, "Run adapter tests")
    result = os.system("python3 -m pytest tests/test_adapters.py -v --tb=short > /dev/null 2>&1")
    if result == 0:
        print_success("Adapter tests passed")
    else:
        print_error("Adapter tests failed")
        phase5_pass = False
    
    print_task(3, "Run all tests")
    result = os.system("python3 -m pytest tests/ -v --tb=short > /dev/null 2>&1")
    if result == 0:
        print_success("All tests passed")
    else:
        print_warning("Some tests failed (check with: python3 -m pytest tests/ -v)")
        phase5_pass = False
    
    # Phase 6: Application Startup
    print_section("PHASE 6: Application Startup Test")
    phase6_pass = True
    
    print_task(1, "Flask application imports correctly")
    try:
        from app import app
        print_success("Flask app imported successfully")
    except Exception as e:
        print_error(f"Failed to import app: {e}")
        phase6_pass = False
    
    print_task(2, "AI Services module loads")
    try:
        from ai_services.config import config
        print_success("AI Services config loaded")
    except Exception as e:
        print_error(f"Failed to load AI Services: {e}")
        phase6_pass = False
    
    # Summary
    print_section("DEPLOYMENT READINESS SUMMARY")
    
    phases = {
        "Phase 1 - Environment Setup": phase1_pass,
        "Phase 2 - Project Structure": phase2_pass,
        "Phase 3 - Configuration": phase3_pass,
        "Phase 4 - Huawei Credentials": phase4_pass,
        "Phase 5 - Test Suite": phase5_pass,
        "Phase 6 - Application": phase6_pass,
    }
    
    all_pass = all(phases.values())
    
    for phase, passed in phases.items():
        status = f"{GREEN}✓ READY{RESET}" if passed else f"{YELLOW}⚠ ATTENTION{RESET}"
        print(f"  {status}: {phase}")
    
    print("\n" + "="*70)
    
    if all_pass:
        print(f"\n{GREEN}✓ DEPLOYMENT READY{RESET}")
        print("\nNext steps:")
        print("  1. Review: HUAWEI_CLOUD_INTEGRATION.md")
        print("  2. Start app: python3 app.py")
        print("  3. Test endpoints: http://localhost:5000")
        print("  4. Monitor logs for cloud service calls")
        return 0
    else:
        print(f"\n{YELLOW}⚠ ATTENTION REQUIRED{RESET}")
        print("\nFailing phases need attention before deployment:")
        print("  • Fix Phase 4 Credentials to enable cloud services")
        print("  • Check Phase 5 & 6 for detailed errors")
        print("\nDeployment can proceed with fallback services (no cloud)")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print_error(f"Checklist error: {e}")
        sys.exit(1)
