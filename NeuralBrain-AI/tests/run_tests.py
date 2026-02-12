#!/usr/bin/env python3
"""
Phase 4 Test Suite Runner
Comprehensive verification and testing for Huawei Cloud integration
"""

import subprocess
import sys
import time
from pathlib import Path

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_section(text):
    """Print formatted section header"""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}>>> {text}{Colors.ENDC}")


def print_success(text):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def run_command(cmd, description=""):
    """Run a command and return success status"""
    if description:
        print_section(description)
    
    print(f"$ {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        return result.returncode == 0, result
    except subprocess.TimeoutExpired:
        print_error(f"Command timed out after 60 seconds")
        return False, None
    except Exception as e:
        print_error(f"Error running command: {e}")
        return False, None


def main():
    """Main test runner"""
    print_header("PHASE 4: COMPREHENSIVE VERIFICATION & TESTING")
    print("Testing Huawei Cloud AI Services Integration\n")
    
    # Get test directory
    test_dir = Path(__file__).parent
    project_dir = test_dir.parent
    
    # Change to project directory
    import os
    os.chdir(project_dir)
    
    results = {}
    test_suites = [
        ("test_config.py", "Configuration Tests"),
        ("test_data_mapper.py", "Data Mapper Tests"),
        ("test_fallback_manager.py", "Fallback Manager Tests"),
        ("test_adapters.py", "Adapter Tests"),
        ("test_integration.py", "Integration Tests"),
        ("test_performance.py", "Performance Tests"),
    ]
    
    total_start = time.time()
    
    # Run each test suite
    for test_file, description in test_suites:
        test_path = test_dir / test_file
        
        if not test_path.exists():
            print_warning(f"Test file not found: {test_file}")
            results[description] = "SKIPPED"
            continue
        
        print_section(description)
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(test_path),
            "-v",
            "--tb=short",
            "-ra"
        ]
        
        start_time = time.time()
        success, result = run_command(cmd)
        elapsed = time.time() - start_time
        
        if success:
            print_success(f"{description} passed in {elapsed:.2f}s")
            results[description] = f"PASSED ({elapsed:.2f}s)"
        else:
            print_error(f"{description} failed")
            results[description] = "FAILED"
    
    total_elapsed = time.time() - total_start
    
    # Print summary
    print_header("TEST SUMMARY")
    
    for test_name, result in results.items():
        if "PASSED" in result:
            print_success(f"{test_name}: {result}")
        elif "FAILED" in result:
            print_error(f"{test_name}: {result}")
        else:
            print_warning(f"{test_name}: {result}")
    
    # Count results
    passed = sum(1 for r in results.values() if "PASSED" in r)
    failed = sum(1 for r in results.values() if "FAILED" in r)
    skipped = sum(1 for r in results.values() if "SKIPPED" in r)
    
    print(f"\n{Colors.BOLD}Total Time: {total_elapsed:.2f}s{Colors.ENDC}")
    print(f"{Colors.BOLD}Results: {passed} passed, {failed} failed, {skipped} skipped{Colors.ENDC}")
    
    # Overall status
    print_header("PHASE 4 STATUS")
    
    if failed == 0:
        print_success("All tests passed! System ready for deployment.")
        return 0
    else:
        print_error(f"{failed} test suite(s) failed. Review output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
