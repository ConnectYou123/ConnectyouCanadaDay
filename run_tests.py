#!/usr/bin/env python3
"""
Test runner script for the Value Investing Stock Finder application.
"""

import sys
import os
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print('='*50)
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ SUCCESS")
        if result.stdout:
            print("Output:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ FAILED")
        print(f"Error: {e}")
        if e.stdout:
            print("Stdout:")
            print(e.stdout)
        if e.stderr:
            print("Stderr:")
            print(e.stderr)
        return False

def main():
    """Run all tests and checks."""
    print("🧪 Running Value Investing Stock Finder Tests")
    print("="*60)
    
    # Add src to Python path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))
    
    # Check if we're in the right directory
    if not (Path(__file__).parent / "src").exists():
        print("❌ Error: src directory not found. Please run from project root.")
        sys.exit(1)
    
    # Install test dependencies
    print("\n📦 Installing test dependencies...")
    run_command("pip install pytest pytest-cov flake8 black bandit safety", "Installing test dependencies")
    
    # Run linting
    print("\n🔍 Running code quality checks...")
    lint_success = run_command(
        "flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics",
        "Flake8 syntax check"
    )
    
    if lint_success:
        run_command(
            "flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics",
            "Flake8 style check"
        )
    
    # Run formatting check
    run_command("black --check src/ tests/", "Black formatting check")
    
    # Run security checks
    print("\n🔒 Running security checks...")
    run_command("bandit -r src/ -f json -o bandit-report.json", "Bandit security check")
    run_command("safety check --json --output safety-report.json", "Safety dependency check")
    
    # Run unit tests
    print("\n🧪 Running unit tests...")
    test_success = run_command(
        "python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing",
        "Unit tests with coverage"
    )
    
    # Run integration tests (if they exist)
    if (Path(__file__).parent / "tests" / "integration").exists():
        print("\n🔗 Running integration tests...")
        run_command(
            "python -m pytest tests/integration/ -v",
            "Integration tests"
        )
    
    # Generate test report
    print("\n📊 Generating test report...")
    if test_success:
        print("✅ All tests passed!")
        print("\n📈 Coverage report generated in htmlcov/index.html")
        print("🔒 Security reports generated:")
        print("   - bandit-report.json")
        print("   - safety-report.json")
    else:
        print("❌ Some tests failed. Please check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
