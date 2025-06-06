from fastapi import FastAPI
from .config import settings
from db import SessionLocal, init_db
from models import ChatSession, ChatMessage, User

app = FastAPI(title="Support Bot")

@app.get("/ping")
def ping():
    return {"message": "pong"}

init_db()
db = SessionLocal()

def create_session(user_id=None):
    session = ChatSession(user_id=user_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session.id

def add_message(session_id, sender, message):
    chat_message = ChatMessage(
        session_id=session_id,
        sender=sender,
        message=message
    )
    db.add(chat_message)
    db.commit()
    return chat_message

def create_user(username):
    user = User(username=username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.id
