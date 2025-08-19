# Makefile for Value Investing Stock Finder

.PHONY: help install test lint format clean build run

# Default target
help:
	@echo "Value Investing Stock Finder - Available Commands:"
	@echo ""
	@echo "  install    - Install dependencies"
	@echo "  test       - Run all tests and checks"
	@echo "  lint       - Run linting checks"
	@echo "  format     - Format code with black"
	@echo "  clean      - Clean build artifacts"
	@echo "  build      - Build the package"
	@echo "  run        - Run the application"
	@echo "  security   - Run security checks"
	@echo "  coverage   - Generate coverage report"

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	pip install -e .

# Run all tests
test:
	@echo "Running tests..."
	python run_tests.py

# Run linting
lint:
	@echo "Running linting checks..."
	flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Format code
format:
	@echo "Formatting code..."
	black src/ tests/

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Build package
build: clean
	@echo "Building package..."
	python setup.py sdist bdist_wheel

# Run the application
run:
	@echo "Running Value Investing Stock Finder..."
	python src/main.py

# Run the web application
web:
	@echo "Starting Value Investing Stock Finder Web Application..."
	@echo "Web interface will be available at: http://localhost:3000"
	python src/main.py

# Run security checks
security:
	@echo "Running security checks..."
	bandit -r src/ -f json -o bandit-report.json
	safety check --json --output safety-report.json

# Generate coverage report
coverage:
	@echo "Generating coverage report..."
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Install development dependencies
install-dev: install
	@echo "Installing development dependencies..."
	pip install pytest pytest-cov flake8 black bandit safety

# Run quick tests (no coverage)
test-quick:
	@echo "Running quick tests..."
	pytest tests/ -v

# Create virtual environment
venv:
	@echo "Creating virtual environment..."
	python -m venv venv
	@echo "Virtual environment created. Activate with:"
	@echo "  source venv/bin/activate  # On Unix/macOS"
	@echo "  venv\\Scripts\\activate     # On Windows"

# Setup development environment
setup-dev: venv
	@echo "Setting up development environment..."
	. venv/bin/activate && pip install -r requirements.txt
	. venv/bin/activate && pip install -e .
	. venv/bin/activate && pip install pytest pytest-cov flake8 black bandit safety
	@echo "Development environment setup complete!"

# Check code quality
quality: lint format
	@echo "Code quality checks completed!"

# Full development cycle
dev-cycle: quality test
	@echo "Development cycle completed!"
