
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.config import APP_NAME, APP_ENV
from app.api.hardware import router as hardware_router
from app.hardware.alert_service import get_alert_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_alert_service().start()   # connects to the Arduino, or falls back to simulate mode
    yield
    get_alert_service().stop()

app = FastAPI(
    title="NemoShield API",
    description="AI-powered Cybersecurity Agent Backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(hardware_router)


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
