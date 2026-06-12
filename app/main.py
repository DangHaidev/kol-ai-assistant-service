from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.routes import chat, health, recommendations
from app.core.config import settings
from app.core.exceptions import (
    ApplicationError,
    application_exception_handler,
    validation_exception_handler,
)
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(title=settings.app_name)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ApplicationError, application_exception_handler)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(recommendations.router, prefix="/api/v1", tags=["recommendations"])
