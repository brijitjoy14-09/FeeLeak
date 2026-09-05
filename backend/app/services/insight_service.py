"""AI executive insight (Prompt 9/12).

The backend first computes validated metrics deterministically; only those
metrics go to the AI. The AI never sees raw datasets and never computes
authoritative numbers. On any AI failure, analytics still works — the caller
gets available=False rather than an error.
"""

import logging

from ..formatting import format_inr
from ..ai.provider import get_provider
from . import analytics_service

logger = logging.getLogger("feeleak.ai")

_ALLOWED_INSIGHT_KEYS = {"summary", "key_findings", "priority_exceptions"}


def _build_metrics():
    summary = analytics_service.get_summary()
    distribution = analytics_service.get_exception_distribution()["data"]
    risks = analytics_service.get_risk_priorities(limit=5)["data"]
    critical_count = sum(1 for r in risks if r["risk_level"] == "CRITICAL")

    top_amount_display = format_inr(distribution[0]["amount"]) if distribution else None
    return {
        "summary": summary,
        "distribution": distribution,
        "risk_priorities": risks,
        "critical_count": critical_count,
        "potential_leakage_display": format_inr(summary["potential_leakage"]),
        "top_amount_display": top_amount_display,
    }


def _validate(insight, metrics):
    if not isinstance(insight, dict):
        raise ValueError("insight is not an object")
    if not isinstance(insight.get("summary"), str) or not insight["summary"].strip():
        raise ValueError("summary missing")
    if not isinstance(insight.get("key_findings"), list):
        raise ValueError("key_findings missing")
    priority = insight.get("priority_exceptions", [])
    if not isinstance(priority, list):
        raise ValueError("priority_exceptions invalid")
    # Grounding: cited exceptions must exist in the risk-priority set we supplied.
    known = {r["exception_id"] for r in metrics["risk_priorities"]}
    for exc_id in priority:
        if exc_id not in known:
            raise ValueError(f"insight cited unknown exception {exc_id}")
    return {k: insight[k] for k in _ALLOWED_INSIGHT_KEYS if k in insight}


def generate_insight(provider=None):
    """Return {available, insight?, metrics?} — never raises on AI failure."""
    metrics = _build_metrics()
    provider = provider or get_provider()
    try:
        raw = provider.generate_insight(metrics)
        insight = _validate(raw, metrics)
    except Exception as exc:  # noqa: BLE001 - AI must never break analytics
        logger.info("ai_insight failed: %s", exc)
        return {
            "available": False,
            "message": "AI insight temporarily unavailable.",
            "metrics": metrics["summary"],
        }
    return {"available": True, "insight": insight, "metrics": metrics["summary"]}
