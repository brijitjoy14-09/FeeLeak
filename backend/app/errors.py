"""Structured application errors and the FastAPI handler that renders them.

All client-facing failures use a consistent envelope:

    {"success": false,
     "error": {"code": "...", "message": "...", "details": {...}}}

This keeps raw stack traces out of API responses and gives the frontend a
stable shape to render.
"""

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """A domain error with a stable code, HTTP status, and optional details."""

    def __init__(self, code: str, message: str, status_code: int = 400, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details

    def to_response(self) -> JSONResponse:
        error = {"code": self.code, "message": self.message}
        if self.details is not None:
            error["details"] = self.details
        return JSONResponse(
            status_code=self.status_code,
            content={"success": False, "error": error},
        )


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return exc.to_response()
