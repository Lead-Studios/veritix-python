from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Dict
from pydantic import BaseModel, ConfigDict

app = FastAPI()

# JWT Config
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"

# Create a reusable security scheme
security = HTTPBearer()


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chat_id: str
    message: str


class LoginResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_token: str


# Token verification function
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # contains user_id or username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Global middleware to secure all routes."""
    if request.url.path in ["/login", "/signup", "/docs", "/openapi.json"]:
        # Allow public routes
        return await call_next(request)

    # Extract Authorization header
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ")[1]
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return await call_next(request)


# Example: Protected Route
@app.get("/user/chat/{chat_id}", response_model=ChatResponse)
async def get_chat(chat_id: str, user: Dict = Depends(verify_token)):
    user_id = user.get("sub")  # typically the user_id
    if not chat_belongs_to_user(chat_id, user_id):
        raise HTTPException(status_code=403, detail="Access denied to this chat session")
    return ChatResponse(chat_id=chat_id, message="Chat retrieved successfully")


def chat_belongs_to_user(chat_id: str, user_id: str) -> bool:
    # Mock validation for example purposes
    # You’d normally check your database here
    return chat_id.startswith(user_id)


@app.post("/login", response_model=LoginResponse)
async def login():
    """Mock login to generate token"""
    user_data = {"sub": "user123"}
    token = jwt.encode(user_data, SECRET_KEY, algorithm=ALGORITHM)
    return LoginResponse(access_token=token)
