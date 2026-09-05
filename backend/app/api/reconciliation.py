"""Reconciliation API routes (thin HTTP layer over the engine)."""

from typing import Optional

from fastapi import APIRouter, Query

from ..errors import AppError
from ..schemas.reconciliation import (
    ResultsResponse,
    RunResponse,
    SummaryResponse,
)
from ..services import reconciliation_service

router = APIRouter(prefix="/api/v1/reconciliation", tags=["reconciliation"])


@router.post("/run", response_model=RunResponse)
async def run():
    result = reconciliation_service.run_reconciliation()
    return RunResponse(run=result["run"], summary=result["summary"])


@router.get("/summary", response_model=SummaryResponse)
async def summary():
    data = reconciliation_service.get_summary()
    if data is None:
        raise AppError(
            "NO_RECONCILIATION",
            "No reconciliation has been run yet.",
            404,
        )
    return SummaryResponse(
        run=data["run"], summary=data["summary"], orphans=data["orphans"]
    )


@router.get("/results", response_model=ResultsResponse)
async def results(
    status: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(default=None, ge=1, le=10000),
):
    all_results = reconciliation_service.get_results()
    if all_results is None:
        raise AppError(
            "NO_RECONCILIATION",
            "No reconciliation has been run yet.",
            404,
        )
    filtered = reconciliation_service.get_results(
        status=status, search=search, limit=limit
    )
    return ResultsResponse(
        total=len(all_results), returned=len(filtered), results=filtered
    )


@router.get("/results/{payment_id}")
async def result(payment_id: str):
    data = reconciliation_service.get_result(payment_id)
    if data is None:
        raise AppError(
            "RESULT_NOT_FOUND",
            f"No reconciliation result for payment '{payment_id}'.",
            404,
            {"payment_id": payment_id},
        )
    return data
