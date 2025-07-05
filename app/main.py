from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from db import SessionLocal, init_db
from models import ChatSession, ChatMessage, User
from app.routers import chat
from app.services import auth_service

app = FastAPI(title="Support Bot")

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

@app.middleware("http")
async def auth_middleware(request: Request, call_next):

    excluded_paths = [
        "/ping",
        "/docs",
        "/openapi.json",
        "/basic_chat/init",
        "/basic_chat/send",
    ]
    

    if request.url.path.startswith("/basic_chat/") and request.url.path.endswith("/history"):
         return await call_next(request)

    if any(request.url.path.startswith(path) for path in excluded_paths):
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


app.include_router(chat.router)
app.include_router(chat.basic_router)
