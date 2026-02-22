# CI/CD Pipeline Documentation

## Overview

This document describes the CI/CD pipeline for the Veritix Python microservice. The pipeline automates code quality checks, testing, security scanning, Docker image building, and deployment.

## Pipeline Stages

### 1. Security Scan
- **Tools**: `safety`, `bandit`
- **Purpose**: Check for security vulnerabilities in dependencies and code
- **Runs on**: All branches and PRs
- **Failure conditions**: Critical security issues found

### 2. Code Quality (Linting)
- **Tools**: `black`, `flake8`, `isort`
- **Purpose**: Ensure consistent code formatting and style
- **Runs on**: All branches and PRs
- **Failure conditions**: Code doesn't meet formatting standards

### 3. Testing
- **Tools**: `pytest` with coverage
- **Purpose**: Run unit and integration tests
- **Runs on**: All branches and PRs
- **Failure conditions**: 
  - Tests fail
  - Coverage drops below 70%
- **Services**: PostgreSQL database for integration tests

### 4. Docker Build
- **Tools**: Docker Buildx
- **Purpose**: Build and test Docker images
- **Runs on**: Push to `main` and `develop` branches
- **Failure conditions**: Docker build fails or container tests fail
- **Features**:
  - Multi-stage builds for optimization
  - Layer caching for faster builds
  - Image scanning and validation

### 5. Deployment
- **Environments**: Staging (develop branch) and Production (main branch)
- **Purpose**: Deploy application to target environments
- **Manual approval**: Required for production deployments
- **Features**:
  - GitHub Releases for production deployments
  - Artifact storage for Docker images

## Configuration Files

### GitHub Actions Workflow (`.github/workflows/ci.yml`)
Main pipeline configuration with:
- Multi-job parallel execution
- Environment-based deployment
- Artifact management
- Security scanning integration

### Linting Configuration
- `pyproject.toml`: Black and isort configuration
- `.flake8`: Flake8 linting rules
- `.safety-policy.yml`: Security scanning policies

### Docker Configuration
- `Dockerfile`: Multi-stage build process
- `docker-compose.test.yml`: Test environment setup

## Environment Variables

### Required Secrets
- `GITHUB_TOKEN`: For Docker registry authentication
- `CODECOV_TOKEN`: For coverage reporting (optional)

### Pipeline Variables
```yaml
PYTHON_VERSION: "3.11"
DOCKER_IMAGE_NAME: veritix-python-app
REGISTRY: ghcr.io
```

## Trigger Events

### Automatic Triggers
- **Push to `main`**: Full pipeline with deployment
- **Push to `develop`**: Full pipeline with staging deployment
- **Pull Request**: Security, linting, and testing only
- **Workflow Dispatch**: Manual trigger for any branch

### Manual Triggers
- GitHub Actions workflow dispatch
- Manual deployment approval

## Test Configuration

### Test Environment
- PostgreSQL 16-alpine database
- Environment variables for test configuration
- Coverage reporting with minimum 70% threshold

### Test Commands
```bash
# Run tests locally
pytest --cov=src --cov-report=term-missing

# Run with Docker
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

## Docker Image Management

### Image Tags
- `latest`: Latest main branch build
- `develop`: Latest develop branch build
- `sha-<commit>`: Specific commit builds
- `v<version>`: Release versions

### Registry
Images are pushed to GitHub Container Registry (GHCR):
`ghcr.io/cybermaxi7/veritix-python`

## Deployment Process

### Staging Deployment
1. Push to `develop` branch
2. Pipeline runs automatically
3. Deploys to staging environment
4. Manual verification required

### Production Deployment
1. Push to `main` branch
2. Pipeline runs automatically
3. Creates GitHub Release
4. Deploys to production environment
5. Manual approval required

## Monitoring and Reporting

### Code Quality
- **Codecov**: Test coverage reporting
- **GitHub Checks**: PR status integration
- **SARIF**: Security scan results

### Performance Metrics
- Build time optimization
- Test execution time
- Docker image size

## Troubleshooting

### Common Issues

1. **Linting Failures**
   ```bash
   # Fix formatting locally
   black .
   isort .
   flake8 .
   ```

2. **Test Failures**
   ```bash
   # Run tests with verbose output
   pytest -v --tb=short
   ```

3. **Docker Build Issues**
   ```bash
   # Build locally for testing
   docker build -t veritix-python-app:test .
   ```

4. **Security Scan Failures**
   ```bash
   # Run security checks locally
   pip install safety bandit
   safety check
   bandit -r src/
   ```

### Debugging Pipeline

1. Check GitHub Actions logs
2. Review test artifacts
3. Examine Docker build logs
4. Verify environment variables

## Best Practices

### For Developers
- Run linting locally before pushing
- Ensure tests pass locally
- Maintain test coverage above 70%
- Follow security guidelines

### For Maintainers
- Monitor pipeline performance
- Review security scan results
- Manage deployment approvals
- Update dependencies regularly

## Future Enhancements

### Planned Improvements
- Integration testing with external services
- Performance benchmarking
- Automated dependency updates
- Advanced deployment strategies (blue-green, canary)
- Enhanced monitoring and alerting

This CI/CD pipeline ensures code quality, security, and reliable deployments for the Veritix Python microservice.