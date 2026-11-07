"""Reusable FastAPI security dependencies.

Keeping shared dependencies in one module gives routers a stable import target
and gives tests a single override point for authentication.
"""

from typing import Annotated

from fastapi import Depends

from app.core.security import current_claims

Claims = Annotated[dict, Depends(current_claims)]
