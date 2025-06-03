from fastapi import FastAPI
from .config import settings

app = FastAPI(title="Support Bot")

@app.get("/ping")
def ping():
    return {"message": "pong"}
