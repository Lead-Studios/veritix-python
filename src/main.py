from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Veritix Microservice",
    version="0.1.0",
    description="A microservice backend for the Veritix platform."
)

@app.get("/")
def read_root():
    return {"message": "Veritix Service is running. Check /health for status."}

@app.get("/health", status_code=200)
def health_check():
    return JSONResponse(content={
        "status": "OK",
        "service": "Veritix Backend",
        "api_version": app.version
    })

# If you run this file directly (e.g., in a local development environment outside Docker):
# if __name__ == "__main__":
#     import uvicorn
#     # Note: host="0.0.0.0" is crucial for Docker development
#     uvicorn.run(app, host="0.0.0.0", port=8000)
