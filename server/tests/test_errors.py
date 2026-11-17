"""B4: every ApiError becomes the one error shape from spec 10.6.

The handler is fetched from the app in main.py, so the test proves the handler that is
actually registered replies with the 10.6 body and the error's status.
"""

import json

from fastapi.responses import JSONResponse

from app.errors import ApiError, error_body
from app.main import app


def test_error_body_is_the_10_6_shape() -> None:
    error = ApiError(404, "not_found", "Plant not found")

    assert error_body(error) == {"error": {"code": "not_found", "message": "Plant not found"}}


def test_registered_handler_replies_with_body_and_status() -> None:
    error = ApiError(401, "unauthorized", "Missing or invalid device key")

    handler = app.exception_handlers[ApiError]
    response = handler(request=None, error=error)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 401
    assert json.loads(response.body) == {
        "error": {"code": "unauthorized", "message": "Missing or invalid device key"}
    }
