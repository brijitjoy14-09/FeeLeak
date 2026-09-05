"""Pydantic models for the Finance Controller Copilot API (Prompt 7)."""

from typing import Any, List, Optional

from pydantic import BaseModel


class CopilotQuery(BaseModel):
    message: str


class CopilotResponse(BaseModel):
    intent: str
    answer: str
    tools_used: List[str]
    data: Optional[Any] = None
