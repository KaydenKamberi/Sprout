"""The one error shape for every API error (spec 10.6).

ApiError carries an HTTP status, a code and a message. The handler registered in
main.py turns any ApiError into the 10.6 body:

    { "error": { "code": ..., "message": ... } }

Later cards (B3, B6 and on) raise ApiError and reuse this shape.
"""

from fastapi import Request
from fastapi.responses import JSONResponse


class ApiError(Exception):
    """An API error with an HTTP status, a code and a message (spec 10.6)."""

    def __init__(self, status: int, code: str, message: str):
        self.status = status
        self.code = code
        self.message = message
        super().__init__(f"{status} {code}: {message}")


def error_body(error: ApiError) -> dict:
    """The 10.6 body for an ApiError: { "error": { "code": ..., "message": ... } }."""
    return {"error": {"code": error.code, "message": error.message}}


def api_error_handler(request: Request, error: ApiError) -> JSONResponse:
    """The FastAPI exception handler registered in main.py for every ApiError."""
    return JSONResponse(status_code=error.status, content=error_body(error))
