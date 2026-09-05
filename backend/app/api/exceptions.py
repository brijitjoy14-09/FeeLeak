"""Exception management API routes (thin layer over the exception service)."""

from typing import Optional

from fastapi import APIRouter, Query

from ..schemas.exceptions import (
    AuditResponse,
    ExceptionListResponse,
    ExceptionModel,
    ExceptionSummary,
    GenerateResponse,
    StatusUpdateRequest,
)
from ..services import audit_service, exception_service

router = APIRouter(prefix="/api/v1/exceptions", tags=["exceptions"])


@router.post("/generate", response_model=GenerateResponse)
async def generate():
    summary = exception_service.generate_exceptions()
    return GenerateResponse(summary=summary)


@router.get("/summary", response_model=ExceptionSummary)
async def summary():
    return exception_service.get_summary()


@router.get("", response_model=ExceptionListResponse)
async def list_exceptions(
    status: Optional[str] = Query(default=None),
    type: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    sort: str = Query(default="priority"),
    limit: Optional[int] = Query(default=None, ge=1, le=10000),
):
    items = exception_service.list_exceptions(
        status=status,
        type=type,
        severity=severity,
        search=search,
        sort=sort,
        limit=limit,
    )
    return ExceptionListResponse(
        total=exception_service.count_all(), returned=len(items), exceptions=items
    )


@router.get("/{exception_id}", response_model=ExceptionModel)
async def get_exception(exception_id: str):
    from ..errors import AppError

    exception = exception_service.get_exception(exception_id)
    if exception is None:
        raise AppError(
            "EXCEPTION_NOT_FOUND",
            f"No exception with id '{exception_id}'.",
            404,
            {"exception_id": exception_id},
        )
    return exception


@router.get("/{exception_id}/audit", response_model=AuditResponse)
async def get_exception_audit(exception_id: str):
    from ..errors import AppError

    if exception_service.get_exception(exception_id) is None:
        raise AppError(
            "EXCEPTION_NOT_FOUND",
            f"No exception with id '{exception_id}'.",
            404,
            {"exception_id": exception_id},
        )
    return AuditResponse(
        exception_id=exception_id,
        events=audit_service.for_exception(exception_id),
    )


@router.patch("/{exception_id}/status", response_model=ExceptionModel)
async def update_status(exception_id: str, body: StatusUpdateRequest):
    return exception_service.update_status(
        exception_id,
        new_status=body.status,
        note=body.note,
        reviewed_by=body.reviewed_by,
    )
