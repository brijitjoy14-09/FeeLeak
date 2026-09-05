"""Deterministic multi-source reconciliation engine.

Primary unit = payment. For each payment we aggregate related refunds, fees,
taxes, and settlements and compute:

    Expected Settlement = Payment - Total Refunds - Total Fees - Total Taxes
    Difference          = Expected Settlement - Actual Settlement
    MATCHED  iff  abs(Difference) <= RECONCILIATION_TOLERANCE

All monetary math uses Decimal (never float). Results are deterministic:
the same input datasets always produce identical results and counts.

Status priority (a payment can have several issues; the FIRST match wins):
    DUPLICATE_PAYMENT -> ORDER_NOT_FOUND -> MISSING_SETTLEMENT -> MISMATCH -> MATCHED

Orphan records (refund/fee/settlement referencing a non-existent payment) are
reported separately and never attached to an unrelated payment.
"""

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from ..config import (
    MONEY_QUANTIZE,
    RECONCILIATION_TOLERANCE,
    SUPPORTED_SOURCES,
)
from ..errors import AppError
from ..stores.data_store import store

ZERO = Decimal("0")

# Statuses produced by the engine.
STATUS_MATCHED = "MATCHED"
STATUS_MISMATCH = "MISMATCH"
STATUS_MISSING_SETTLEMENT = "MISSING_SETTLEMENT"
STATUS_ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
STATUS_DUPLICATE_PAYMENT = "DUPLICATE_PAYMENT"


def _money(value: Decimal) -> str:
    """Serialize a Decimal to a 2dp string for API output."""
    return str(value.quantize(MONEY_QUANTIZE))


def _index_by(records, key):
    """Group records into {key_value: [records...]} preserving order."""
    index = defaultdict(list)
    for record in records:
        index[record.get(key, "")].append(record)
    return index


def _duplicate_ids(records, key):
    """Return the set of id values that appear more than once."""
    counts = defaultdict(int)
    for record in records:
        counts[record.get(key, "")] += 1
    return {value for value, count in counts.items() if count > 1}


def _sum(records, field):
    total = ZERO
    for record in records:
        value = record.get(field)
        if isinstance(value, Decimal):
            total += value
    return total


def require_datasets():
    """Ensure all five source datasets are loaded, else raise MISSING_DATASET."""
    missing = [s for s in SUPPORTED_SOURCES if not store.has_dataset(s)]
    if missing:
        raise AppError(
            "MISSING_DATASET",
            "Required financial datasets are missing.",
            400,
            {"missing_sources": missing},
        )


def _reconcile_payment(payment, indexes, duplicate_payment_ids):
    payment_id = payment.get("payment_id", "")
    order_id = payment.get("order_id", "")
    payment_amount = payment.get("payment_amount", ZERO)
    if not isinstance(payment_amount, Decimal):
        payment_amount = ZERO

    refunds = indexes["refunds_by_payment"].get(payment_id, [])
    fees = indexes["fees_by_payment"].get(payment_id, [])
    settlements = indexes["settlements_by_payment"].get(payment_id, [])

    total_refund = _sum(refunds, "refund_amount")
    total_fee = _sum(fees, "fee_amount")
    total_tax = _sum(fees, "tax_amount")
    actual_settlement = _sum(settlements, "settlement_amount")

    expected_settlement = payment_amount - total_refund - total_fee - total_tax
    difference = expected_settlement - actual_settlement

    order_found = order_id in indexes["orders_by_id"]
    settlement_count = len(settlements)

    # Deterministic status priority.
    if payment_id in duplicate_payment_ids:
        status = STATUS_DUPLICATE_PAYMENT
    elif not order_found:
        status = STATUS_ORDER_NOT_FOUND
    elif settlement_count == 0:
        status = STATUS_MISSING_SETTLEMENT
    elif abs(difference) > RECONCILIATION_TOLERANCE:
        status = STATUS_MISMATCH
    else:
        status = STATUS_MATCHED

    order = indexes["orders_by_id"].get(order_id, [None])[0]
    order_amount = order.get("order_amount") if order else None

    return {
        "payment_id": payment_id,
        "order_id": order_id,
        "order_found": order_found,
        "order_amount": _money(order_amount) if isinstance(order_amount, Decimal) else None,
        "payment_amount": _money(payment_amount),
        "total_refund": _money(total_refund),
        "total_fee": _money(total_fee),
        "total_tax": _money(total_tax),
        "expected_settlement": _money(expected_settlement),
        "actual_settlement": _money(actual_settlement),
        "difference": _money(difference),
        "abs_difference": _money(abs(difference)),
        "refund_count": len(refunds),
        "fee_count": len(fees),
        "settlement_count": settlement_count,
        "status": status,
        # Raw Decimals kept for summary aggregation (stripped before API output).
        "_expected": expected_settlement,
        "_actual": actual_settlement,
        "_difference": difference,
    }


def _orphans(records, payment_ids, ref_field):
    """Records whose ref payment_id is not a known payment."""
    return [r for r in records if r.get(ref_field, "") not in payment_ids]


def run_reconciliation():
    """Run reconciliation over the currently loaded datasets and store results."""
    require_datasets()
    started_at = datetime.now().astimezone()

    payments = store.records("payments")
    orders = store.records("orders")
    refunds = store.records("refunds")
    fees = store.records("fees")
    settlements = store.records("settlements")

    payment_ids = {p.get("payment_id", "") for p in payments}
    indexes = {
        "orders_by_id": _index_by(orders, "order_id"),
        "refunds_by_payment": _index_by(refunds, "payment_id"),
        "fees_by_payment": _index_by(fees, "payment_id"),
        "settlements_by_payment": _index_by(settlements, "payment_id"),
    }
    duplicate_payment_ids = _duplicate_ids(payments, "payment_id")

    results = [
        _reconcile_payment(p, indexes, duplicate_payment_ids) for p in payments
    ]

    orphan_settlements = _orphans(settlements, payment_ids, "payment_id")
    orphan_refunds = _orphans(refunds, payment_ids, "payment_id")
    orphan_fees = _orphans(fees, payment_ids, "payment_id")

    # ---- Summary (computed from results; never hardcoded) ----
    def count(status):
        return sum(1 for r in results if r["status"] == status)

    total_expected = sum((r["_expected"] for r in results), ZERO)
    total_actual = sum((r["_actual"] for r in results), ZERO)
    total_difference = total_expected - total_actual

    summary = {
        "total_payments": len(results),
        "matched": count(STATUS_MATCHED),
        "mismatched": count(STATUS_MISMATCH),
        "missing_settlement": count(STATUS_MISSING_SETTLEMENT),
        "order_not_found": count(STATUS_ORDER_NOT_FOUND),
        "duplicate_payment": count(STATUS_DUPLICATE_PAYMENT),
        "orphan_records": {
            "settlements": len(orphan_settlements),
            "refunds": len(orphan_refunds),
            "fees": len(orphan_fees),
        },
        "total_expected_settlement": _money(total_expected),
        "total_actual_settlement": _money(total_actual),
        "total_difference": _money(total_difference),
    }

    completed_at = datetime.now().astimezone()
    run = {
        "run_id": f"RUN-{started_at.strftime('%Y%m%d-%H%M%S')}",
        "status": "completed",
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
        "total_payments": len(results),
    }

    # Strip internal Decimal helpers before storing for API consumption.
    public_results = [
        {k: v for k, v in r.items() if not k.startswith("_")} for r in results
    ]
    results_by_id = {}
    for r in public_results:
        results_by_id.setdefault(r["payment_id"], r)

    reconciliation = {
        "run": run,
        "summary": summary,
        "results": public_results,
        "results_by_id": results_by_id,
        "orphans": {
            "settlements": [_serialize_orphan(o, "settlement") for o in orphan_settlements],
            "refunds": [_serialize_orphan(o, "refund") for o in orphan_refunds],
            "fees": [_serialize_orphan(o, "fee") for o in orphan_fees],
        },
    }
    store.set_reconciliation(reconciliation)
    return {"run": run, "summary": summary}


def _serialize_orphan(record, kind):
    id_field = f"{kind}_id"
    amount_field = f"{kind}_amount"
    amount = record.get(amount_field)
    return {
        "id": record.get(id_field, ""),
        "payment_id": record.get("payment_id", ""),
        "amount": _money(amount) if isinstance(amount, Decimal) else None,
        "kind": kind,
    }


def get_summary():
    reconciliation = store.get_reconciliation()
    if not reconciliation:
        return None
    return {
        "run": reconciliation["run"],
        "summary": reconciliation["summary"],
        "orphans": reconciliation["orphans"],
    }


def get_results(status=None, search=None, limit=None):
    reconciliation = store.get_reconciliation()
    if not reconciliation:
        return None
    results = reconciliation["results"]
    if status:
        results = [r for r in results if r["status"] == status]
    if search:
        needle = search.strip().lower()
        results = [
            r
            for r in results
            if needle in r["payment_id"].lower() or needle in r["order_id"].lower()
        ]
    if limit is not None:
        results = results[:limit]
    return results


def get_result(payment_id):
    reconciliation = store.get_reconciliation()
    if not reconciliation:
        return None
    return reconciliation["results_by_id"].get(payment_id)
