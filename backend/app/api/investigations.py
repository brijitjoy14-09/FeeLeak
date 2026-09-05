"""AI investigation API routes (Prompt 6).

Nested under exceptions: investigate a specific exception and fetch its latest
investigation. The exception is never modified by these endpoints.
"""

from fastapi import APIRouter

from ..errors import AppError
from ..schemas.investigation import InvestigationResponse, InvestigationResult
from ..services import investigation_service

router = APIRouter(prefix="/api/v1/exceptions", tags=["investigations"])


@router.post("/{exception_id}/investigate", response_model=InvestigationResponse)
async def investigate(exception_id: str):
    investigation = investigation_service.investigate(exception_id)
    return InvestigationResponse(investigation=InvestigationResult(**investigation))


@router.get("/{exception_id}/investigation", response_model=InvestigationResponse)
async def get_investigation(exception_id: str):
    investigation = investigation_service.get_latest_investigation(exception_id)
    if investigation is None:
        raise AppError(
            "INVESTIGATION_NOT_FOUND",
            f"No investigation has been run for exception '{exception_id}'.",
            404,
            {"exception_id": exception_id},
        )
    return InvestigationResponse(investigation=InvestigationResult(**investigation))
