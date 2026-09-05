"""Exception management service (Prompt 5) — fully deterministic.

Turns reconciliation results into reviewable exceptions with affected amount,
potential leakage, severity, and priority. All money uses `Decimal`. Generation
is idempotent (stable IDs, preserves review state). No AI here.
"""

from datetime import datetime
from decimal import Decimal

from ..config import (
    ACTIVE_EXCEPTION_STATUSES,
    DEMO_REVIEWER,
    EXCEPTION_TRANSITIONS,
    EXCEPTION_TYPE_WEIGHTS,
    MONEY_QUANTIZE,
    ORPHAN_KIND_TO_EXCEPTION_TYPE,
    REASON_REQUIRED_STATUSES,
    RECON_STATUS_TO_EXCEPTION_TYPE,
    RISK_AGE_CAP_DAYS,
    RISK_AMOUNT_CAP,
    RISK_LEVEL_THRESHOLDS,
    RISK_SEVERITY_SCORE,
    RISK_STATUS_SCORE,
    RISK_WEIGHTS,
    SEVERITY_RANK,
    SEVERITY_THRESHOLDS,
)
from ..errors import AppError
from ..stores.data_store import store
from . import audit_service

ZERO = Decimal("0")
LIFECYCLE_FIELDS = (
    "status",
    "created_at",
    "reviewed_at",
    "reviewed_by",
    "resolution",
    "escalation_reason",
    "rejection_reason",
)


def compute_risk(amount, severity, age_days, status):
    """Deterministic 0-100 risk score + level + explainable drivers.

    Same inputs always produce the same score. Risk is a *prioritization*
    signal, NOT a probability of fraud.
    """
    amount = amount or ZERO
    amount_score = min(amount / RISK_AMOUNT_CAP, Decimal("1")) * 100
    severity_score = Decimal(RISK_SEVERITY_SCORE.get(severity, 0))
    age_score = min(Decimal(age_days) / Decimal(RISK_AGE_CAP_DAYS), Decimal("1")) * 100
    status_score = Decimal(RISK_STATUS_SCORE.get(status, 0))

    raw = (
        RISK_WEIGHTS["amount"] * amount_score
        + RISK_WEIGHTS["severity"] * severity_score
        + RISK_WEIGHTS["age"] * age_score
        + RISK_WEIGHTS["status"] * status_score
    )
    score = int(raw.to_integral_value(rounding="ROUND_HALF_UP"))
    score = max(0, min(100, score))

    level = "CRITICAL"
    for name, upper in RISK_LEVEL_THRESHOLDS:
        if score < upper:
            level = name
            break

    drivers = [f"Discrepancy: {_money(amount)}", f"{severity} severity"]
    if status in ACTIVE_EXCEPTION_STATUSES:
        drivers.append("Escalated status" if status == "ESCALATED" else "Unresolved status")
    if age_days >= 7:
        drivers.append("Aging exception")
    return score, level, drivers


def _age_days(created_at):
    if not created_at:
        return 0
    try:
        created = datetime.fromisoformat(created_at)
        return max(0, (datetime.now().astimezone() - created).days)
    except ValueError:
        return 0


def _apply_risk(exception):
    """(Re)compute and attach risk fields based on current status/amount."""
    amount = _dec(exception.get("affected_amount")) or ZERO
    score, level, drivers = compute_risk(
        amount, exception["severity"], _age_days(exception.get("created_at")),
        exception["status"],
    )
    exception["risk_score"] = score
    exception["risk_level"] = level
    exception["risk_drivers"] = drivers
    return exception


def _dec(value):
    if value is None or value == "":
        return None
    return Decimal(str(value))


def _money(value):
    if value is None:
        return None
    return str(value.quantize(MONEY_QUANTIZE))


def _now():
    return datetime.now().astimezone().isoformat()


def compute_severity(amount: Decimal) -> str:
    """Severity from a monetary magnitude (leakage, else affected amount)."""
    amount = amount or ZERO
    for level, upper in SEVERITY_THRESHOLDS:
        if amount < upper:
            return level
    return "CRITICAL"


def compute_priority(severity: str, exception_type: str, impact: Decimal) -> int:
    """Deterministic priority score (higher = surfaced first).

    Ordering: severity band, then financial impact, then per-type weight.
    """
    impact = impact or ZERO
    impact_paise = int((impact.quantize(MONEY_QUANTIZE)) * 100)
    severity_rank = SEVERITY_RANK[severity]
    type_weight = EXCEPTION_TYPE_WEIGHTS.get(exception_type, 0)
    return severity_rank * 10**15 + impact_paise * 100 + type_weight


def _finalize(exception_type, base):
    """Attach severity/priority given affected_amount + potential_leakage."""
    leakage = base["_leakage"]
    affected = base["_affected"]
    impact = leakage if leakage > ZERO else affected
    severity = compute_severity(impact)
    priority = compute_priority(severity, exception_type, impact)
    base.update(
        {
            "type": exception_type,
            "severity": severity,
            "priority": priority,
            "affected_amount": _money(affected),
            "potential_leakage": _money(leakage),
        }
    )
    for key in ("_leakage", "_affected"):
        base.pop(key, None)
    return base


def _build_from_result(result):
    """Build an exception from a non-matched payment reconciliation result."""
    status = result["status"]
    exception_type = RECON_STATUS_TO_EXCEPTION_TYPE[status]

    expected = _dec(result["expected_settlement"])
    actual = _dec(result["actual_settlement"])
    difference = _dec(result["difference"])
    payment_amount = _dec(result["payment_amount"])

    if exception_type == "AMOUNT_MISMATCH":
        leakage = max(difference, ZERO)
        affected = abs(difference)
        desc = (
            f"Settlement differs from expected by {_money(abs(difference))} "
            f"for payment {result['payment_id']}."
        )
    elif exception_type == "MISSING_SETTLEMENT":
        leakage = max(difference, ZERO)
        affected = expected
        desc = (
            f"No settlement recorded; expected {_money(expected)} for payment "
            f"{result['payment_id']}."
        )
    else:  # ORDER_NOT_FOUND, DUPLICATE_PAYMENT -> data-integrity, leakage 0
        leakage = ZERO
        affected = payment_amount
        if exception_type == "ORDER_NOT_FOUND":
            desc = (
                f"Payment {result['payment_id']} references order "
                f"{result['order_id']} which is not in the orders dataset."
            )
        else:
            desc = f"Duplicate payment identifier {result['payment_id']} detected."

    base = {
        "exception_id": f"EXC-{result['payment_id']}",
        "payment_id": result["payment_id"],
        "order_id": result["order_id"] or None,
        "source_kind": "payment",
        "record_id": None,
        "expected_amount": _money(expected),
        "actual_amount": _money(actual),
        "difference": _money(difference),
        "description": desc,
        "_leakage": leakage,
        "_affected": affected,
    }
    return _finalize(exception_type, base)


def _build_from_orphan(orphan):
    """Build a data-integrity exception from an orphan record (leakage 0)."""
    kind = orphan["kind"]  # singular: settlement | refund | fee
    exception_type = ORPHAN_KIND_TO_EXCEPTION_TYPE[kind]
    amount = _dec(orphan["amount"]) or ZERO

    base = {
        "exception_id": f"EXC-{orphan['id']}",
        "payment_id": orphan["payment_id"] or None,
        "order_id": None,
        "source_kind": "orphan",
        "record_id": orphan["id"],
        "expected_amount": None,
        "actual_amount": _money(amount),
        "difference": None,
        "description": (
            f"Orphan {kind} {orphan['id']} references payment "
            f"{orphan['payment_id']} which does not exist."
        ),
        "_leakage": ZERO,
        "_affected": amount,
    }
    return _finalize(exception_type, base)


def _merge_lifecycle(existing, fresh):
    """Preserve review state across regeneration; refresh computed fields."""
    if existing is None:
        fresh.setdefault("status", "OPEN")
        fresh["created_at"] = _now()
        fresh["reviewed_at"] = None
        fresh["reviewed_by"] = None
        fresh["resolution"] = None
        fresh["escalation_reason"] = None
        fresh["rejection_reason"] = None
        return fresh
    for field in LIFECYCLE_FIELDS:
        fresh[field] = existing.get(field)
    return fresh


def generate_exceptions():
    """(Re)generate exceptions from the latest reconciliation run (idempotent)."""
    recon = store.get_reconciliation()
    if not recon:
        raise AppError(
            "RECONCILIATION_NOT_RUN",
            "Run reconciliation before generating exceptions.",
            400,
        )

    existing = store.get_exceptions()
    fresh = {}
    newly_created = []

    def add(exc):
        exc_id = exc["exception_id"]
        prior = existing.get(exc_id)
        merged = _merge_lifecycle(prior, exc)
        _apply_risk(merged)
        fresh[exc_id] = merged
        if prior is None:
            newly_created.append(merged)

    for result in recon["results"]:
        if result["status"] == "MATCHED":
            continue
        add(_build_from_result(result))

    for items in recon["orphans"].values():
        for orphan in items:
            add(_build_from_orphan(orphan))

    store.set_exceptions(fresh)
    for exc in newly_created:
        audit_service.record(
            "EXCEPTION_CREATED", exc["exception_id"], "system",
            detail=f"{exc['type']} · {exc['severity']} · risk {exc['risk_score']}",
        )
    return get_summary()


# ---- Read APIs ------------------------------------------------------------

_SORT_KEYS = {
    "priority": lambda e: e["priority"],
    "potential_leakage": lambda e: _dec(e["potential_leakage"]) or ZERO,
    "created_at": lambda e: e["created_at"] or "",
}


def list_exceptions(
    status=None, type=None, severity=None, search=None, sort="priority", limit=None
):
    items = list(store.get_exceptions().values())

    if status:
        items = [e for e in items if e["status"] == status]
    if type:
        items = [e for e in items if e["type"] == type]
    if severity:
        items = [e for e in items if e["severity"] == severity]
    if search:
        needle = search.strip().lower()
        items = [
            e
            for e in items
            if needle in e["exception_id"].lower()
            or needle in (e["payment_id"] or "").lower()
            or needle in (e["order_id"] or "").lower()
        ]

    key = _SORT_KEYS.get(sort, _SORT_KEYS["priority"])
    items.sort(key=key, reverse=True)
    if limit is not None:
        items = items[:limit]
    return items


def get_exception(exception_id):
    return store.get_exception(exception_id)


def count_all():
    return len(store.get_exceptions())


def get_summary():
    items = list(store.get_exceptions().values())
    counts = {"OPEN": 0, "IN_REVIEW": 0, "RESOLVED": 0, "ESCALATED": 0, "REJECTED": 0}
    severity_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    type_dist = {}
    total_affected = ZERO
    total_leakage = ZERO

    for e in items:
        counts[e["status"]] = counts.get(e["status"], 0) + 1
        if e["status"] in ACTIVE_EXCEPTION_STATUSES:  # active KPIs exclude resolved/rejected
            severity_dist[e["severity"]] = severity_dist.get(e["severity"], 0) + 1
            type_dist[e["type"]] = type_dist.get(e["type"], 0) + 1
            total_affected += _dec(e["affected_amount"]) or ZERO
            total_leakage += _dec(e["potential_leakage"]) or ZERO

    active = counts["OPEN"] + counts["IN_REVIEW"] + counts["ESCALATED"]
    return {
        "total_exceptions": len(items),
        "open": counts["OPEN"],
        "in_review": counts["IN_REVIEW"],
        "resolved": counts["RESOLVED"],
        "escalated": counts["ESCALATED"],
        "rejected": counts["REJECTED"],
        "active_exceptions": active,
        "total_affected_amount": _money(total_affected),
        "potential_leakage": _money(total_leakage),
        "severity_distribution": severity_dist,
        "type_distribution": type_dist,
    }


# ---- Review workflow ------------------------------------------------------

def update_status(exception_id, new_status, note=None, reviewed_by=None):
    exception = store.get_exception(exception_id)
    if exception is None:
        raise AppError(
            "EXCEPTION_NOT_FOUND",
            f"No exception with id '{exception_id}'.",
            404,
            {"exception_id": exception_id},
        )

    if new_status not in EXCEPTION_TRANSITIONS:
        raise AppError(
            "INVALID_STATUS",
            f"Unknown status '{new_status}'.",
            422,
            {"allowed": list(EXCEPTION_TRANSITIONS.keys())},
        )

    current = exception["status"]
    if new_status not in EXCEPTION_TRANSITIONS[current]:
        raise AppError(
            "INVALID_TRANSITION",
            f"Cannot move an exception from {current} to {new_status}.",
            422,
            {"from": current, "to": new_status,
             "allowed": sorted(EXCEPTION_TRANSITIONS[current])},
        )

    note = (note or "").strip()
    if new_status in REASON_REQUIRED_STATUSES and not note:
        code = {
            "RESOLVED": "RESOLUTION_REQUIRED",
            "ESCALATED": "ESCALATION_REASON_REQUIRED",
            "REJECTED": "REJECTION_REASON_REQUIRED",
        }[new_status]
        raise AppError(code, f"A reason is required to move to {new_status}.", 422)

    actor = reviewed_by or DEMO_REVIEWER
    exception["status"] = new_status
    exception["reviewed_at"] = _now()
    exception["reviewed_by"] = actor
    if new_status == "RESOLVED":
        exception["resolution"] = note
    elif new_status == "ESCALATED":
        exception["escalation_reason"] = note
    elif new_status == "REJECTED":
        exception["rejection_reason"] = note

    _apply_risk(exception)  # status affects the risk score
    store.put_exception(exception)

    event_type = {
        "IN_REVIEW": "REVIEW_STARTED",
        "RESOLVED": "RESOLVED",
        "ESCALATED": "ESCALATED",
        "REJECTED": "REJECTED",
    }.get(new_status, "STATUS_CHANGED")
    audit_service.record(
        event_type, exception_id, actor,
        detail=f"{current} → {new_status}", reason=note or None,
    )
    return exception
