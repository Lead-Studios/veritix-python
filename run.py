import uvicorn
from src.main import app # noqa: F401

if __name__ == "__main__":
    from src.config import get_settings
    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        timeout_graceful_shutdown=settings.SHUTDOWN_TIMEOUT_SECONDS
    )


