"""Analytics API routes (Prompt 9) — thin layer over analytics_service."""

from typing import Optional

from fastapi import APIRouter, Query

from ..schemas.analytics import (
    AnalyticsSummary,
    DistributionResponse,
    InsightResponse,
    LeakageTrendResponse,
    RiskPrioritiesResponse,
)
from ..services import analytics_service, insight_service

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def summary(
    status: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    classification: Optional[str] = Query(default=None),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
):
    return analytics_service.get_summary(
        status=status, severity=severity, classification=classification,
        start_date=start_date, end_date=end_date,
    )


@router.get("/leakage-trend", response_model=LeakageTrendResponse)
async def leakage_trend(granularity: str = Query(default="day")):
    return analytics_service.get_leakage_trend(granularity=granularity)


@router.get("/exception-distribution", response_model=DistributionResponse)
async def exception_distribution(
    status: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
):
    return analytics_service.get_exception_distribution(
        status=status, severity=severity, start_date=start_date, end_date=end_date,
    )


@router.get("/risk-priorities", response_model=RiskPrioritiesResponse)
async def risk_priorities(
    limit: Optional[int] = Query(default=None, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
):
    return analytics_service.get_risk_priorities(
        limit=limit, status=status, severity=severity,
    )


@router.get("/insight", response_model=InsightResponse)
async def insight():
    return insight_service.generate_insight()
