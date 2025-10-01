import uvicorn
from src.main import app # noqa: F401

if __name__ == "__main__":
    uvicorn.run("run:app", host="0.0.0.0", port=8000)


