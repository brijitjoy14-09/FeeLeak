"""Deterministic finance analytics (Prompt 9).

Reads the EXISTING reconciliation results + exceptions (no second reconciliation
engine). All authoritative numbers are computed here in the backend using
`Decimal`; the frontend never computes them. Risk scoring is delegated to the
deterministic `exception_service.compute_risk` used at generation time.
"""

from decimal import Decimal

from ..config import (
    ACTIVE_EXCEPTION_STATUSES,
    MONEY_QUANTIZE,
    RISK_PRIORITIES_DEFAULT_LIMIT,
    RISK_PRIORITIES_MAX_LIMIT,
)
from ..errors import AppError
from ..stores.data_store import store

ZERO = Decimal("0")


def _dec(value):
    if value in (None, ""):
        return ZERO
    return Decimal(str(value))


def _money(value):
    return str(value.quantize(MONEY_QUANTIZE))


def _pct(part, whole, places=2):
    if not whole:
        return 0.0
    return round(part / whole * 100, places)


def _payment_date_index():
    """payment_id -> payment_date (business date), from the payments dataset."""
    index = {}
    for record in store.records("payments"):
        index[record.get("payment_id")] = record.get("payment_date")
    return index


def _exception_date(exception, date_index):
    return date_index.get(exception.get("payment_id"))


def _validate_date_range(start_date, end_date):
    if start_date and end_date and start_date > end_date:
        raise AppError(
            "INVALID_DATE_RANGE",
            "start_date must not be after end_date.",
            422,
            {"start_date": start_date, "end_date": end_date},
        )


def _filter_exceptions(status=None, severity=None, classification=None,
                       start_date=None, end_date=None):
    _validate_date_range(start_date, end_date)
    date_index = _payment_date_index()
    items = list(store.get_exceptions().values())
    out = []
    for e in items:
        if status and e["status"] != status:
            continue
        if severity and e["severity"] != severity:
            continue
        if classification and e["type"] != classification:
            continue
        if start_date or end_date:
            date = _exception_date(e, date_index)
            if date is None:
                continue
            if start_date and date < start_date:
                continue
            if end_date and date > end_date:
                continue
        out.append(e)
    return out


def get_summary(status=None, severity=None, classification=None,
                start_date=None, end_date=None):
    recon = store.get_reconciliation()
    transactions = recon["summary"]["total_payments"] if recon else 0
    matched = recon["summary"]["matched"] if recon else 0

    items = _filter_exceptions(status, severity, classification, start_date, end_date)
    total = len(items)
    resolved = sum(1 for e in items if e["status"] == "RESOLVED")
    escalated = sum(1 for e in items if e["status"] == "ESCALATED")
    rejected = sum(1 for e in items if e["status"] == "REJECTED")
    active = sum(1 for e in items if e["status"] in ACTIVE_EXCEPTION_STATUSES)
    leakage = sum(
        (_dec(e["potential_leakage"]) for e in items
         if e["status"] in ACTIVE_EXCEPTION_STATUSES),
        ZERO,
    )

    return {
        "transactions_processed": transactions,
        "matched_transactions": matched,
        "match_rate": _pct(matched, transactions, 1),
        "total_exceptions": total,
        "unresolved_exceptions": active,
        "resolved_exceptions": resolved,
        "escalated_exceptions": escalated,
        "rejected_exceptions": rejected,
        "exception_rate": _pct(total, transactions, 1),
        "resolution_rate": _pct(resolved, total, 2),
        "potential_leakage": _money(leakage),
    }


def get_leakage_trend(granularity="day"):
    """Daily potential-leakage trend keyed on payment business date.

    Returns available=False when no dated leakage points exist (e.g. no
    timestamps) rather than fabricating history.
    """
    date_index = _payment_date_index()
    buckets = {}
    for e in store.get_exceptions().values():
        if e["status"] not in ACTIVE_EXCEPTION_STATUSES:
            continue
        leakage = _dec(e["potential_leakage"])
        if leakage <= ZERO:
            continue
        date = _exception_date(e, date_index)
        if not date:
            continue
        # Normalize to a date-only key.
        day = date[:10]
        buckets[day] = buckets.get(day, ZERO) + leakage

    if not buckets:
        return {
            "granularity": granularity,
            "available": False,
            "message": "Trend data unavailable — no dated leakage in the current data.",
            "data": [],
        }
    data = [{"date": day, "potential_leakage": _money(amount)}
            for day, amount in sorted(buckets.items())]
    return {"granularity": granularity, "available": True, "data": data}


def get_exception_distribution(status=None, severity=None, start_date=None,
                               end_date=None):
    """Count + financial impact per classification, ranked by impact desc."""
    items = _filter_exceptions(status, severity, None, start_date, end_date)
    grouped = {}
    for e in items:
        key = e["type"]
        bucket = grouped.setdefault(key, {"count": 0, "amount": ZERO})
        bucket["count"] += 1
        bucket["amount"] += _dec(e["affected_amount"])
    data = [
        {"classification": key, "count": v["count"], "amount": _money(v["amount"])}
        for key, v in grouped.items()
    ]
    # Rank primarily by total financial impact (discrepancy), then count.
    data.sort(key=lambda d: (Decimal(d["amount"]), d["count"]), reverse=True)
    return {"data": data}


def get_risk_priorities(limit=None, status=None, severity=None):
    """Highest-risk UNRESOLVED exceptions, deterministically ordered."""
    if limit is None:
        limit = RISK_PRIORITIES_DEFAULT_LIMIT
    if limit < 1 or limit > RISK_PRIORITIES_MAX_LIMIT:
        raise AppError(
            "INVALID_LIMIT",
            f"limit must be between 1 and {RISK_PRIORITIES_MAX_LIMIT}.",
            422,
            {"limit": limit},
        )

    items = [
        e for e in store.get_exceptions().values()
        if e["status"] in ACTIVE_EXCEPTION_STATUSES
        and (not status or e["status"] == status)
        and (not severity or e["severity"] == severity)
    ]
    # Deterministic ordering: risk desc, discrepancy desc, oldest first.
    items.sort(
        key=lambda e: (
            -e["risk_score"],
            -_dec(e["affected_amount"]),
            e["created_at"] or "",
        )
    )
    top = items[:limit]
    data = [
        {
            "exception_id": e["exception_id"],
            "risk_score": e["risk_score"],
            "risk_level": e["risk_level"],
            "risk_drivers": e.get("risk_drivers", []),
            "discrepancy": e["affected_amount"],
            "potential_leakage": e["potential_leakage"],
            "classification": e["type"],
            "severity": e["severity"],
            "status": e["status"],
        }
        for e in top
    ]
    return {"total": len(items), "returned": len(data), "data": data}


def get_resolution_performance():
    items = list(store.get_exceptions().values())
    total = len(items)
    resolved = sum(1 for e in items if e["status"] == "RESOLVED")
    escalated = sum(1 for e in items if e["status"] == "ESCALATED")
    rejected = sum(1 for e in items if e["status"] == "REJECTED")
    active = sum(1 for e in items if e["status"] in ACTIVE_EXCEPTION_STATUSES)
    return {
        "total_exceptions": total,
        "resolved": resolved,
        "escalated": escalated,
        "rejected": rejected,
        "active": active,
        "resolution_rate": _pct(resolved, total, 2),
    }
