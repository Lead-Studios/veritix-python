from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from db import SessionLocal, init_db
from models import ChatSession, ChatMessage, User
from app.routers import chat
from app.services import auth_service

app = FastAPI(title="Support Bot")

# CORS (optional, can adjust as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
def ping():
    return {"message": "pong"}

# Authentication Middleware
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path == "/ping":
        return await call_next(request)
    if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi"):
        return await call_next(request)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Missing or invalid token"})
    token = auth_header.split(" ", 1)[1]
    token_data = auth_service.verify_token(token)
    if not token_data or not token_data.user_id:
        return JSONResponse(status_code=401, content={"detail": "Invalid token"})
    request.state.user_id = token_data.user_id
    request.state.role = token_data.role
    return await call_next(request)

init_db()

# Include chat router
app.include_router(chat.router)
