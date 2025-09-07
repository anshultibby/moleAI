#!/usr/bin/env python3
"""
Test runner for moleAI backend

This script provides convenient ways to run different types of tests:
- Unit tests (fast, no external dependencies)
- Integration tests (require API keys)
- All tests
- Specific test modules
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and return the result"""
    if description:
        print(f"🚀 {description}")
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    return result.returncode == 0


def check_environment():
    """Check if the test environment is properly set up"""
    print("🔍 Checking test environment...")
    
    # Check if pytest is installed
    try:
        import pytest
        print(f"✅ pytest {pytest.__version__} found")
    except ImportError:
        print("❌ pytest not found. Install with: pip install pytest")
        return False
    
    # Check if required packages are available
    required_packages = ['pydantic', 'requests', 'python-dotenv']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} found")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} not found")
    
    if missing_packages:
        print(f"Install missing packages with: pip install {' '.join(missing_packages)}")
        return False
    
    # Check for API keys (for integration tests)
    api_key = os.getenv("JINA_AI_API_KEY")
    if api_key:
        print("✅ JINA_AI_API_KEY found (integration tests will run)")
    else:
        print("⚠️ JINA_AI_API_KEY not found (integration tests will be skipped)")
    
    return True


def run_unit_tests():
    """Run fast unit tests only"""
    cmd = ["python", "-m", "pytest", "tests/", "-m", "not integration", "-v"]
    return run_command(cmd, "Running unit tests")


def run_integration_tests():
    """Run integration tests that require API keys"""
    if not os.getenv("JINA_AI_API_KEY"):
        print("⚠️ JINA_AI_API_KEY not found - skipping integration tests")
        return True
    
    cmd = ["python", "-m", "pytest", "tests/", "-m", "integration", "-v"]
    return run_command(cmd, "Running integration tests")


def run_all_tests():
    """Run all tests"""
    cmd = ["python", "-m", "pytest", "tests/", "-v"]
    return run_command(cmd, "Running all tests")


def run_specific_test(test_path):
    """Run a specific test file or test function"""
    cmd = ["python", "-m", "pytest", test_path, "-v"]
    return run_command(cmd, f"Running specific test: {test_path}")


def run_coverage():
    """Run tests with coverage reporting"""
    try:
        import coverage
        print("✅ coverage.py found")
    except ImportError:
        print("❌ coverage.py not found. Install with: pip install coverage")
        return False
    
    cmd = ["python", "-m", "pytest", "tests/", "--cov=app", "--cov-report=html", "--cov-report=term"]
    return run_command(cmd, "Running tests with coverage")


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="moleAI Backend Test Runner")
    parser.add_argument(
        "test_type", 
        choices=["unit", "integration", "all", "coverage", "check"],
        nargs="?",
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--file", 
        help="Run specific test file (e.g., tests/app/modules/test_serp.py)"
    )
    parser.add_argument(
        "--function",
        help="Run specific test function (e.g., tests/app/modules/test_serp.py::test_basic_search)"
    )
    
    args = parser.parse_args()
    
    print("🧪 moleAI Backend Test Runner")
    print("=" * 50)
    
    # Check environment first
    if not check_environment():
        print("\n❌ Environment check failed!")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    
    success = True
    
    if args.file:
        success = run_specific_test(args.file)
    elif args.function:
        success = run_specific_test(args.function)
    elif args.test_type == "check":
        print("✅ Environment check completed successfully!")
    elif args.test_type == "unit":
        success = run_unit_tests()
    elif args.test_type == "integration":
        success = run_integration_tests()
    elif args.test_type == "coverage":
        success = run_coverage()
    else:  # all
        success = run_all_tests()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Tests completed successfully!")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
