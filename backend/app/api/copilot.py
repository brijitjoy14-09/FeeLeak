"""Finance Controller Copilot API (Prompt 7)."""

from fastapi import APIRouter

from ..errors import AppError
from ..schemas.copilot import CopilotQuery, CopilotResponse
from ..services import copilot_service

router = APIRouter(prefix="/api/v1/copilot", tags=["copilot"])


@router.post("/query", response_model=CopilotResponse)
async def query(body: CopilotQuery):
    message = (body.message or "").strip()
    if not message:
        raise AppError("EMPTY_QUERY", "Ask the Copilot a question.", 422)
    return copilot_service.query(message)
