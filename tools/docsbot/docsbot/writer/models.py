from __future__ import annotations

from pydantic import BaseModel, Field


class WriteOutcome(BaseModel):
    written: list[str] = Field(default_factory=list)
    autogen: list[str] = Field(default_factory=list)
    skipped: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
