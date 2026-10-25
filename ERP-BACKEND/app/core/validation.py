"""Request-level validation middleware for API routers.

Validates content-type for write operations and enforces maximum body size.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

MAX_BODY_SIZE = 10 * 1024 * 1024  # 10MB


async def validate_request(request: Request, call_next):
    """Validate incoming requests before routing.

    - POST/PUT/PATCH must have Content-Type: application/json
    - Request body must not exceed MAX_BODY_SIZE
    """
    if request.method in ["POST", "PUT", "PATCH"]:
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            return JSONResponse(
                status_code=415,
                content={
                    "error": {
                        "code": "UNSUPPORTED_MEDIA_TYPE",
                        "message": "Content-Type must be application/json",
                    }
                },
            )

    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BODY_SIZE:
        return JSONResponse(
            status_code=413,
            content={
                "error": {
                    "code": "PAYLOAD_TOO_LARGE",
                    "message": "Request body too large",
                }
            },
        )

    return await call_next(request)
