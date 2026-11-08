
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.config import APP_NAME, APP_ENV
from app.api.hardware import router as hardware_router
from app.api.agent_routes import router as agent_router
from app.api.events import router as events_router
from app.api.analysis import router as analysis_router
from app.api.alerts import router as alerts_router
from app.api.dashboard import router as dashboard_router
from app.api.decision import router as decision_router
from app.api.traces import router as traces_router
from app.hardware.alert_service import get_alert_service
from app.api.exception_handlers import register_exception_handlers


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

register_exception_handlers(app)

app.include_router(hardware_router)
app.include_router(agent_router)
app.include_router(events_router)
app.include_router(analysis_router)
app.include_router(alerts_router)
app.include_router(dashboard_router)
app.include_router(decision_router)
app.include_router(traces_router)

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
