
from fastapi import FastAPI
from app.config import APP_NAME, APP_ENV

app = FastAPI(
    title="NemoShield API",
    description="AI-powered Cybersecurity Agent Backend",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "NemoShield Backend is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": app.version
    }
