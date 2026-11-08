
import logging

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.models.api_schemas import ErrorDetail, ErrorResponse


logger = logging.getLogger(__name__)


def error_json(status_code: int, code: str, message: str):
    response = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
        )
    )

    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(),
    )


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ):
        codes = {
            400: "BAD_REQUEST",
            404: "NOT_FOUND",
            502: "BAD_GATEWAY",
            503: "SERVICE_UNAVAILABLE",
        }

        code = codes.get(exc.status_code, "HTTP_ERROR")

        message = (
            exc.detail
            if isinstance(exc.detail, str)
            else "Request failed"
        )

        return error_json(
            exc.status_code,
            code,
            message,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        return error_json(
            422,
            "VALIDATION_ERROR",
            "Request validation failed",
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception,
    ):
        logger.error(
            "Unhandled API exception",
            exc_info=(type(exc), exc, exc.__traceback__),
        )

        return error_json(
            500,
            "INTERNAL_SERVER_ERROR",
            "An unexpected server error occurred",
        )
