"""Pydantic models for AI investigation results (Prompt 6).

Used both to VALIDATE untrusted AI output and to serialize stored results.
Invalid classification / action / confidence / malformed evidence all raise a
ValidationError, which the service converts into a controlled API error.
"""

from typing import List, Optional

from pydantic import BaseModel, field_validator

from ..config import AI_ACTIONS, AI_CLASSIFICATIONS, SUPPORTED_SOURCES

# Non-record evidence sources the AI is allowed to cite.
_EXTRA_EVIDENCE_SOURCES = {"reconciliation", "exception"}
_ALLOWED_EVIDENCE_SOURCES = set(SUPPORTED_SOURCES) | _EXTRA_EVIDENCE_SOURCES


class EvidenceRef(BaseModel):
    source: str
    id: str
    amount: Optional[str] = None
    note: Optional[str] = None

    @field_validator("source")
    @classmethod
    def _source_allowed(cls, value):
        if value not in _ALLOWED_EVIDENCE_SOURCES:
            raise ValueError(f"invalid evidence source: {value}")
        return value

    @field_validator("id")
    @classmethod
    def _id_present(cls, value):
        if not value or not str(value).strip():
            raise ValueError("evidence id required")
        return value


class InvestigationResult(BaseModel):
    classification: str
    summary: str
    root_cause: str
    confidence: int
    evidence: List[EvidenceRef]
    missing_evidence: List[str] = []
    recommended_action: str
    reason: str
    # Assigned/overwritten by the service (never trusted from the AI).
    investigation_id: Optional[str] = None
    exception_id: Optional[str] = None
    created_at: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None

    @field_validator("classification")
    @classmethod
    def _classification_allowed(cls, value):
        if value not in AI_CLASSIFICATIONS:
            raise ValueError(f"invalid classification: {value}")
        return value

    @field_validator("recommended_action")
    @classmethod
    def _action_allowed(cls, value):
        if value not in AI_ACTIONS:
            raise ValueError(f"invalid recommended_action: {value}")
        return value

    @field_validator("confidence")
    @classmethod
    def _confidence_range(cls, value):
        if value < 0 or value > 100:
            raise ValueError("confidence must be between 0 and 100")
        return value


class InvestigationResponse(BaseModel):
    success: bool = True
    investigation: InvestigationResult
