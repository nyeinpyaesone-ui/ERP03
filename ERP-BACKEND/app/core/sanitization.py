"""Input sanitization helpers for ERP03."""

import bleach
from pydantic import BaseModel, field_validator


class SanitizedModel(BaseModel):
    """Base model that sanitizes all string fields by stripping HTML tags."""

    @field_validator("*", mode="before")
    @classmethod
    def sanitize_strings(cls, value):
        if isinstance(value, str):
            return bleach.clean(value, tags=[], strip=True)
        return value
