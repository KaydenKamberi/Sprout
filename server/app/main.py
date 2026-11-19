"""The Sprout FastAPI app.

No endpoints yet. Checkpoints B3 onward add them, following spec sections 8 and 10.
"""

from fastapi import FastAPI

from app.errors import ApiError, api_error_handler

app = FastAPI(title="Sprout")

app.add_exception_handler(ApiError, api_error_handler)
