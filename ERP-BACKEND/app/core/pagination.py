"""Shared pagination primitives for list endpoints."""

from dataclasses import dataclass

from pydantic import BaseModel, Field


class PageParams(BaseModel):
    """Query-parameter contract for paginated reads."""

    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


@dataclass(frozen=True, slots=True)
class Page:
    items: list[object]
    limit: int
    offset: int
    total: int

    @property
    def has_more(self) -> bool:
        return self.offset + len(self.items) < self.total
