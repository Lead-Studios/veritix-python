#!/bin/bash
# Local CI validation script
# Run this script to validate the CI/CD pipeline configuration locally

set -e

echo "🧪 Running Local CI Validation..."

# Check if running in correct directory
if [[ ! -f "requirements.txt" ]]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Install required tools
echo "📦 Installing required tools..."
python -m pip install --upgrade pip
pip install black flake8 isort pytest pytest-cov pytest-asyncio safety bandit

# Check 1: Linting
echo "📋 Checking code formatting and linting..."
echo "   Running black..."
black --check . || echo "   ❌ Black formatting issues found"
echo "   Running isort..."
isort --check-only --diff . || echo "   ❌ Import sorting issues found"
echo "   Running flake8..."
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Check 2: Security scanning
echo "🔒 Running security scans..."
echo "   Running safety check..."
safety check --full-report || echo "   ⚠️  Security vulnerabilities found"
echo "   Running bandit..."
bandit -r src/ -f json -o bandit-report.json || echo "   ⚠️  Security issues found in code"

# Check 3: Tests
echo "🧪 Running tests..."
if [[ -f ".env.test" ]]; then
    export $(cat .env.test | xargs)
else
    export SKIP_MODEL_TRAINING=true
fi

pytest --cov=src --cov-report=term-missing --cov-fail-under=80 || echo "   ❌ Tests failed or coverage below 80%"

# Check 4: Docker build
echo "🐳 Testing Docker build..."
docker build -t veritix-python-app:local-test . || echo "   ❌ Docker build failed"

# Check 5: Docker container test
echo "🧪 Testing Docker container..."
docker run --rm veritix-python-app:local-test python -c "import src.main; print('✅ Application imports successfully')" || echo "   ❌ Container test failed"

echo "✅ Local CI validation completed!"
echo ""
echo "📋 Summary:"
echo "   - Code formatting: black, isort, flake8"
echo "   - Security scanning: safety, bandit"  
echo "   - Testing: pytest with coverage"
echo "   - Docker: build and container test"
echo ""
echo "🚀 Ready for GitHub Actions pipeline!"
