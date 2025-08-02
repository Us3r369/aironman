#!/usr/bin/env python3
"""
Comprehensive test runner for AIronman application.
"""

import sys
import subprocess
import argparse
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ SUCCESS")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ FAILED")
        print(f"Error: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def run_unit_tests():
    """Run unit tests."""
    return run_command(
        ["python", "-m", "pytest", "tests/", "-v", "--tb=short", "-m", "unit"],
        "Unit Tests"
    )


def run_integration_tests():
    """Run integration tests."""
    return run_command(
        ["python", "-m", "pytest", "tests/", "-v", "--tb=short", "-m", "integration"],
        "Integration Tests"
    )


def run_agent_tests():
    """Run agent-specific tests."""
    return run_command(
        ["python", "-m", "pytest", "tests/test_recovery_agent.py", "-v", "--tb=short"],
        "Agent Tests"
    )


def run_api_tests():
    """Run API endpoint tests."""
    return run_command(
        ["python", "-m", "pytest", "tests/test_api.py", "-v", "--tb=short"],
        "API Tests"
    )


def run_database_tests():
    """Run database-related tests."""
    return run_command(
        ["python", "-m", "pytest", "tests/test_database.py", "-v", "--tb=short"],
        "Database Tests"
    )


def run_coverage_tests():
    """Run tests with coverage reporting."""
    return run_command(
        [
            "python", "-m", "pytest", "tests/", 
            "--cov=api", "--cov=services", "--cov=utils", "--cov=agents",
            "--cov-report=term-missing", "--cov-report=html:htmlcov",
            "--cov-fail-under=80", "-v"
        ],
        "Coverage Tests"
    )


def run_linting():
    """Run code linting."""
    linting_passed = True
    
    # Black formatting check
    if not run_command(["black", "--check", "--diff", "."], "Black Formatting Check"):
        linting_passed = False
    
    # isort import sorting check
    if not run_command(["isort", "--check-only", "--diff", "."], "Import Sorting Check"):
        linting_passed = False
    
    # flake8 linting
    if not run_command(["flake8", "--max-line-length=88", "--extend-ignore=E203,W503", "."], "Flake8 Linting"):
        linting_passed = False
    
    # bandit security check
    if not run_command(["bandit", "-r", "."], "Bandit Security Check"):
        linting_passed = False
    
    return linting_passed


def run_all_tests():
    """Run all tests and checks."""
    print("🚀 Starting comprehensive test suite...")
    
    all_passed = True
    
    # Run linting first
    if not run_linting():
        all_passed = False
    
    # Run unit tests
    if not run_unit_tests():
        all_passed = False
    
    # Run agent tests
    if not run_agent_tests():
        all_passed = False
    
    # Run API tests
    if not run_api_tests():
        all_passed = False
    
    # Run database tests
    if not run_database_tests():
        all_passed = False
    
    # Run coverage tests
    if not run_coverage_tests():
        all_passed = False
    
    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Code quality checks passed")
        print("✅ Unit tests passed")
        print("✅ Agent tests passed")
        print("✅ API tests passed")
        print("✅ Database tests passed")
        print("✅ Coverage requirements met")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please fix the failing tests before proceeding.")
    print('='*60)
    
    return all_passed


def setup_pre_commit():
    """Set up pre-commit hooks."""
    print("🔧 Setting up pre-commit hooks...")
    
    # Install pre-commit
    if not run_command(["pip", "install", "pre-commit"], "Install pre-commit"):
        return False
    
    # Install pre-commit hooks
    if not run_command(["pre-commit", "install"], "Install pre-commit hooks"):
        return False
    
    # Run pre-commit on all files
    if not run_command(["pre-commit", "run", "--all-files"], "Run pre-commit on all files"):
        return False
    
    print("✅ Pre-commit hooks set up successfully!")
    return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="AIronman Test Runner")
    parser.add_argument(
        "--mode",
        choices=["unit", "integration", "agent", "api", "database", "coverage", "lint", "all", "setup"],
        default="all",
        help="Test mode to run"
    )
    parser.add_argument(
        "--setup-pre-commit",
        action="store_true",
        help="Set up pre-commit hooks"
    )
    
    args = parser.parse_args()
    
    if args.setup_pre_commit:
        setup_pre_commit()
        return
    
    if args.mode == "unit":
        success = run_unit_tests()
    elif args.mode == "integration":
        success = run_integration_tests()
    elif args.mode == "agent":
        success = run_agent_tests()
    elif args.mode == "api":
        success = run_api_tests()
    elif args.mode == "database":
        success = run_database_tests()
    elif args.mode == "coverage":
        success = run_coverage_tests()
    elif args.mode == "lint":
        success = run_linting()
    elif args.mode == "all":
        success = run_all_tests()
    else:
        print(f"Unknown mode: {args.mode}")
        return 1
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 