"""AI investigation orchestration (Prompt 6).

Pipeline: find exception → require reconciliation evidence → build bundle →
call provider (retry once) → parse → schema-validate → evidence-ground →
apply confidence safety rules → store. The exception is NEVER modified here;
AI is advisory only and can never auto-resolve or change financial values.
"""

import logging
from datetime import datetime

from pydantic import ValidationError

from ..config import (
    AI_MODEL,
    CONFIDENCE_AUTO_RESOLVE,
    CONFIDENCE_REVIEW,
)
from ..errors import AppError
from ..schemas.investigation import InvestigationResult
from ..stores.data_store import store
from ..ai.provider import get_provider
from . import audit_service, evidence_service

logger = logging.getLogger("feeleak.ai")


def _now():
    return datetime.now().astimezone().isoformat()


def _call_provider(provider, bundle):
    """Call the provider with one retry. AppErrors propagate unchanged."""
    last_error = None
    for _attempt in range(2):
        try:
            return provider.investigate(bundle)
        except AppError:
            raise
        except Exception as exc:  # noqa: BLE001 - convert to controlled error
            last_error = exc
    raise AppError(
        "AI_PROVIDER_ERROR",
        "The AI provider failed to complete the investigation.",
        502,
        {"detail": str(last_error)} if last_error else None,
    )


def _validate_grounding(result: InvestigationResult, index: dict):
    """Every cited record must exist in the bundle with a matching amount."""
    for ref in result.evidence:
        key = (ref.source, ref.id)
        if key not in index:
            raise AppError(
                "AI_GROUNDING_FAILED",
                "The AI referenced a record that is not in the evidence bundle.",
                422,
                {"source": ref.source, "id": ref.id},
            )
        if not evidence_service.amount_matches(ref.amount, index[key]):
            raise AppError(
                "AI_GROUNDING_FAILED",
                "The AI cited an amount that does not match the evidence.",
                422,
                {"source": ref.source, "id": ref.id, "claimed": ref.amount},
            )


def _enforce_action(confidence: int, proposed: str) -> str:
    """Backend-enforced confidence -> action safety."""
    if confidence < CONFIDENCE_REVIEW:
        return "ESCALATE"
    if confidence < CONFIDENCE_AUTO_RESOLVE:
        return "REVIEW" if proposed == "AUTO_RESOLVE" else proposed
    return proposed  # >= AUTO_RESOLVE threshold: proposal stands (still advisory)


def investigate(exception_id: str, provider=None):
    exception = store.get_exception(exception_id)
    if exception is None:
        raise AppError(
            "EXCEPTION_NOT_FOUND",
            f"No exception with id '{exception_id}'.",
            404,
            {"exception_id": exception_id},
        )

    if store.get_reconciliation() is None:
        raise AppError(
            "RECONCILIATION_EVIDENCE_NOT_AVAILABLE",
            "Reconciliation evidence is not available for this exception.",
            409,
        )

    bundle, index = evidence_service.build_evidence_bundle(exception)
    if exception.get("source_kind") == "payment" and bundle["reconciliation"] is None:
        raise AppError(
            "RECONCILIATION_EVIDENCE_NOT_AVAILABLE",
            "Reconciliation evidence is not available for this exception.",
            409,
        )

    provider = provider or get_provider()
    provider_name = getattr(provider, "name", "unknown")
    model = getattr(provider, "model", AI_MODEL)

    started = datetime.now()
    raw = _call_provider(provider, bundle)

    if not isinstance(raw, dict):
        _log(exception_id, None, provider_name, model, started, False, "not_a_dict")
        raise AppError(
            "AI_INVALID_RESPONSE",
            "The AI response was not a valid JSON object.",
            502,
        )

    try:
        result = InvestigationResult(**raw)
    except ValidationError as exc:
        _log(exception_id, None, provider_name, model, started, False, "schema")
        raise AppError(
            "AI_VALIDATION_FAILED",
            "The AI response failed schema validation.",
            422,
            {"errors": exc.errors(include_url=False)[:5]},
        ) from exc

    _validate_grounding(result, index)

    # Safety: enforce confidence -> action. AI never resolves the exception.
    result.recommended_action = _enforce_action(
        result.confidence, result.recommended_action
    )

    history = store.get_investigations(exception_id)
    result.investigation_id = f"INV-{exception_id}-{len(history) + 1}"
    result.exception_id = exception_id
    result.created_at = _now()
    result.provider = provider_name
    result.model = model

    stored = result.model_dump()
    store.add_investigation(exception_id, stored)
    audit_service.record(
        "AI_INVESTIGATION", exception_id, f"ai:{provider_name}",
        detail=(
            f"{result.classification} · confidence {result.confidence} · "
            f"recommends {result.recommended_action}"
        ),
    )
    _log(exception_id, result.investigation_id, provider_name, model, started, True, "ok")
    return stored


def get_latest_investigation(exception_id: str):
    exception = store.get_exception(exception_id)
    if exception is None:
        raise AppError(
            "EXCEPTION_NOT_FOUND",
            f"No exception with id '{exception_id}'.",
            404,
            {"exception_id": exception_id},
        )
    return store.get_latest_investigation(exception_id)


def _log(exception_id, investigation_id, provider, model, started, success, validation):
    """Log useful metadata only — never keys or full financial datasets."""
    duration_ms = int((datetime.now() - started).total_seconds() * 1000)
    logger.info(
        "ai_investigation exception=%s investigation=%s provider=%s model=%s "
        "duration_ms=%s success=%s validation=%s",
        exception_id,
        investigation_id,
        provider,
        model,
        duration_ms,
        success,
        validation,
    )
