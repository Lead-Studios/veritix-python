import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends, Request
from pydantic import ValidationError
from ..schemas import TokenData
from ..models import User
from ..db import get_db
from sqlalchemy.orm import Session

# Secret key and algorithm for JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        username: str = payload.get("username")
        role: str = payload.get("role")
        if user_id is None or username is None:
            return None
        return TokenData(user_id=user_id, username=username, role=role)
    except (JWTError, ValidationError):
        return None


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    # Check for token in Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")
    token = auth_header.split(" ", 1)[1]
    token_data = verify_token(token)
    if not token_data or not token_data.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user or not getattr(user, "is_active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user
