"""Pydantic models for the exception management API."""

from typing import Dict, List, Optional

from pydantic import BaseModel


class ExceptionModel(BaseModel):
    exception_id: str
    payment_id: Optional[str] = None
    order_id: Optional[str] = None
    source_kind: str
    record_id: Optional[str] = None
    type: str
    status: str
    severity: str
    priority: int
    expected_amount: Optional[str] = None
    actual_amount: Optional[str] = None
    difference: Optional[str] = None
    affected_amount: str
    potential_leakage: str
    risk_score: int
    risk_level: str
    risk_drivers: List[str] = []
    description: str
    created_at: str
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    resolution: Optional[str] = None
    escalation_reason: Optional[str] = None
    rejection_reason: Optional[str] = None


class ExceptionSummary(BaseModel):
    total_exceptions: int
    open: int
    in_review: int
    resolved: int
    escalated: int
    rejected: int
    active_exceptions: int
    total_affected_amount: str
    potential_leakage: str
    severity_distribution: Dict[str, int]
    type_distribution: Dict[str, int]


class AuditEvent(BaseModel):
    audit_id: str
    exception_id: Optional[str] = None
    event_type: str
    actor: str
    timestamp: str
    detail: Optional[str] = None
    reason: Optional[str] = None


class AuditResponse(BaseModel):
    exception_id: Optional[str] = None
    events: List[AuditEvent]


class GenerateResponse(BaseModel):
    success: bool = True
    summary: ExceptionSummary


class ExceptionListResponse(BaseModel):
    total: int
    returned: int
    exceptions: List[ExceptionModel]


class StatusUpdateRequest(BaseModel):
    status: str
    note: Optional[str] = None
    reviewed_by: Optional[str] = None
