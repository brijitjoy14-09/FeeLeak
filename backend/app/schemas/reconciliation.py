"""Pydantic response models for the reconciliation API."""

from typing import List, Optional

from pydantic import BaseModel


class RunMetadata(BaseModel):
    run_id: str
    status: str
    started_at: str
    completed_at: str
    total_payments: int


class OrphanCounts(BaseModel):
    settlements: int
    refunds: int
    fees: int


class ReconciliationSummary(BaseModel):
    total_payments: int
    matched: int
    mismatched: int
    missing_settlement: int
    order_not_found: int
    duplicate_payment: int
    orphan_records: OrphanCounts
    total_expected_settlement: str
    total_actual_settlement: str
    total_difference: str


class RunResponse(BaseModel):
    success: bool = True
    run: RunMetadata
    summary: ReconciliationSummary


class ReconciliationResult(BaseModel):
    payment_id: str
    order_id: str
    order_found: bool
    order_amount: Optional[str] = None
    payment_amount: str
    total_refund: str
    total_fee: str
    total_tax: str
    expected_settlement: str
    actual_settlement: str
    difference: str
    abs_difference: str
    refund_count: int
    fee_count: int
    settlement_count: int
    status: str


class ResultsResponse(BaseModel):
    total: int
    returned: int
    results: List[ReconciliationResult]


class OrphanRecord(BaseModel):
    id: str
    payment_id: str
    amount: Optional[str] = None
    kind: str


class SummaryResponse(BaseModel):
    run: RunMetadata
    summary: ReconciliationSummary
    orphans: dict[str, List[OrphanRecord]]
