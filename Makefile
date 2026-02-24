# Makefile for CI/CD tasks

.PHONY: help install lint test security docker validate

# Default target
help:
	@echo "Veritix Python - CI/CD Tasks"
	@echo "============================"
	@echo "Available commands:"
	@echo "  make install     - Install development dependencies"
	@echo "  make lint        - Run code formatting and linting"
	@echo "  make test        - Run tests with coverage"
	@echo "  make security    - Run security scans"
	@echo "  make docker      - Build and test Docker image"
	@echo "  make validate    - Run full CI validation"
	@echo "  make clean       - Clean build artifacts"

# Install development dependencies
install:
	pip install -r requirements.txt
	pip install black flake8 isort pytest pytest-cov pytest-asyncio safety bandit

# Code formatting and linting
lint:
	@echo "Running code formatting checks..."
	black --check .
	isort --check-only --diff .
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Run tests
test:
	@echo "Running tests with coverage..."
	SKIP_MODEL_TRAINING=true pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# Security scanning
security:
	@echo "Running security scans..."
	safety check --full-report
	bandit -r src/ -f json -o bandit-report.json

# Docker build and test
docker:
	@echo "Building Docker image..."
	docker build -t veritix-python-app:local .
	@echo "Testing Docker container..."
	docker run --rm veritix-python-app:local python -c "import src.main; print('✅ Application imports successfully')"

# Full CI validation
validate:
	@echo "Running full CI validation..."
	./scripts/validate-ci.sh

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	rm -f .coverage coverage.xml
	rm -f bandit-report.json
	rm -rf build/ dist/ *.egg-info/
	docker rmi veritix-python-app:local veritix-python-app:local-test 2>/dev/null || true

# Format code (fix issues)
format:
	black .
	isort .

# Run tests in Docker with PostgreSQL
test-docker:
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Run all checks
check: lint test security

# Development setup
dev-setup: install lint test
	@echo "Development environment ready!"
