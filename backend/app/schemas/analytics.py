"""Pydantic response models for the analytics API (Prompt 9)."""

from typing import List, Optional

from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    transactions_processed: int
    matched_transactions: int
    match_rate: float
    total_exceptions: int
    unresolved_exceptions: int
    resolved_exceptions: int
    escalated_exceptions: int
    rejected_exceptions: int
    exception_rate: float
    resolution_rate: float
    potential_leakage: str


class LeakagePoint(BaseModel):
    date: str
    potential_leakage: str


class LeakageTrendResponse(BaseModel):
    granularity: str
    available: bool
    message: Optional[str] = None
    data: List[LeakagePoint] = []


class DistributionItem(BaseModel):
    classification: str
    count: int
    amount: str


class DistributionResponse(BaseModel):
    data: List[DistributionItem]


class RiskPriorityItem(BaseModel):
    exception_id: str
    risk_score: int
    risk_level: str
    risk_drivers: List[str] = []
    discrepancy: str
    potential_leakage: str
    classification: str
    severity: str
    status: str


class RiskPrioritiesResponse(BaseModel):
    total: int
    returned: int
    data: List[RiskPriorityItem]


class InsightBody(BaseModel):
    summary: str
    key_findings: List[str] = []
    priority_exceptions: List[str] = []


class InsightResponse(BaseModel):
    available: bool
    message: Optional[str] = None
    insight: Optional[InsightBody] = None
    metrics: Optional[AnalyticsSummary] = None
