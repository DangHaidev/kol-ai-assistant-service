from fastapi import FastAPI

from app.api.routes import chat, health, recommendations
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(title=settings.app_name)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(recommendations.router, prefix="/api/v1", tags=["recommendations"])
