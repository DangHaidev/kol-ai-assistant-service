from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApplicationError(Exception):
    """Base application exception."""


class ConversationNotFoundError(ApplicationError):
    """Raised when a conversation cannot be found for the given brand."""


class BackendUnavailableError(ApplicationError):
    """Raised when the backend candidate search cannot be completed."""


def build_error_response(code: str, message: str, details: object | None = None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
        }
    }


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    del request
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=build_error_response(
            "INVALID_REQUEST",
            "Invalid request",
            exc.errors(),
        ),
    )


async def application_exception_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    del request
    if isinstance(exc, ConversationNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=build_error_response("CONVERSATION_NOT_FOUND", str(exc), None),
        )
    if isinstance(exc, BackendUnavailableError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=build_error_response("BACKEND_UNAVAILABLE", str(exc), None),
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=build_error_response("RECOMMENDATION_FAILED", str(exc), None),
    )
