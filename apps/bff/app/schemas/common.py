from typing import Any, Literal

from pydantic import BaseModel, Field


class PlaceholderListResponse(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    source: Literal["placeholder"] = "placeholder"
    message: str
