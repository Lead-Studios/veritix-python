import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.config import settings

# auto_error=False allows us to manually trigger a 401 if the header is completely missing
bearer_scheme = HTTPBearer(auto_error=False)

def require_service_key(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """Validates the SERVICE_API_KEY for internal service-to-service calls."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token"
        )
        
    if not secrets.compare_digest(credentials.credentials, settings.SERVICE_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid service token"
        )
        
    return credentials.credentials

def require_admin_key(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """Validates the ADMIN_API_KEY for admin and analytics endpoints."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token"
        )
        
    if not secrets.compare_digest(credentials.credentials, settings.ADMIN_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin token"
        )
        
    return credentials.credentials