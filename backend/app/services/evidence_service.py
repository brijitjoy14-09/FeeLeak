"""Builds a focused, traceable evidence bundle for an exception (Prompt 6).

Only records relevant to the exception are included — never the whole dataset.
Every item carries its source and record id so AI output can be grounded back
to real records. Returns (bundle, grounding_index) where grounding_index maps
(source, id) -> Decimal amount (or None) for validating AI evidence claims.
"""

from decimal import Decimal

from ..config import MONEY_QUANTIZE
from ..stores.data_store import store

# Amount field per source, used to build the grounding index.
_AMOUNT_FIELD = {
    "orders": "order_amount",
    "payments": "payment_amount",
    "refunds": "refund_amount",
    "fees": "fee_amount",
    "settlements": "settlement_amount",
}
_ID_FIELD = {
    "orders": "order_id",
    "payments": "payment_id",
    "refunds": "refund_id",
    "fees": "fee_id",
    "settlements": "settlement_id",
}


def _serialize(record):
    out = {}
    for key, value in record.items():
        out[key] = str(value) if isinstance(value, Decimal) else value
    return out


def _first(records, field, value):
    for record in records:
        if record.get(field) == value:
            return record
    return None


def _all(records, field, value):
    return [r for r in records if r.get(field) == value]


def build_evidence_bundle(exception):
    """Return (bundle, grounding_index) for a given exception."""
    payment_id = exception.get("payment_id")
    recon = store.get_reconciliation()
    recon_result = None
    if recon and payment_id:
        recon_result = recon["results_by_id"].get(payment_id)

    payments = store.records("payments")
    orders = store.records("orders")
    refunds = store.records("refunds")
    fees = store.records("fees")
    settlements = store.records("settlements")

    payment = _first(payments, "payment_id", payment_id) if payment_id else None
    order = None
    if payment:
        order = _first(orders, "order_id", payment.get("order_id"))

    related_refunds = _all(refunds, "payment_id", payment_id) if payment_id else []
    related_fees = _all(fees, "payment_id", payment_id) if payment_id else []
    related_settlements = (
        _all(settlements, "payment_id", payment_id) if payment_id else []
    )

    # For orphan exceptions the referenced payment does not exist; include the
    # orphan record itself as the primary evidence, looked up by its record id.
    orphan_record = None
    if exception.get("source_kind") == "orphan":
        kind = exception["type"]
        source = {
            "ORPHAN_SETTLEMENT": ("settlements", settlements),
            "ORPHAN_REFUND": ("refunds", refunds),
            "ORPHAN_FEE": ("fees", fees),
        }[kind]
        source_name, records = source
        orphan_record = _first(records, _ID_FIELD[source_name], exception["record_id"])

    bundle = {
        "exception": {
            "exception_id": exception["exception_id"],
            "type": exception["type"],
            "payment_id": payment_id,
            "order_id": exception.get("order_id"),
            "expected_amount": exception.get("expected_amount"),
            "actual_amount": exception.get("actual_amount"),
            "difference": exception.get("difference"),
            "potential_leakage": exception.get("potential_leakage"),
            "description": exception.get("description"),
        },
        "reconciliation": recon_result,
        "order": _serialize(order) if order else None,
        "payment": _serialize(payment) if payment else None,
        "refunds": [_serialize(r) for r in related_refunds],
        "fees": [_serialize(f) for f in related_fees],
        "settlements": [_serialize(s) for s in related_settlements],
        "orphan_record": _serialize(orphan_record) if orphan_record else None,
    }

    # ---- grounding index: (source, id) -> Decimal amount (or None) ----
    index = {}

    def add(source, record):
        if not record:
            return
        rid = record.get(_ID_FIELD[source])
        amount_field = _AMOUNT_FIELD[source]
        raw = record.get(amount_field)
        amount = None
        if isinstance(raw, Decimal):
            amount = raw
        elif raw not in (None, ""):
            amount = Decimal(str(raw))
        index[(source, rid)] = amount

    add("payments", payment)
    add("orders", order)
    for r in related_refunds:
        add("refunds", r)
    for f in related_fees:
        add("fees", f)
    for s in related_settlements:
        add("settlements", s)
    if orphan_record:
        source_name = {
            "ORPHAN_SETTLEMENT": "settlements",
            "ORPHAN_REFUND": "refunds",
            "ORPHAN_FEE": "fees",
        }[exception["type"]]
        add(source_name, orphan_record)

    # Non-record citations the AI may reference.
    index[("reconciliation", payment_id)] = None
    index[("exception", exception["exception_id"])] = None

    return bundle, index


def amount_matches(claimed, actual):
    """True if a claimed evidence amount matches the grounded amount."""
    if claimed is None or actual is None:
        return True  # nothing to contradict
    try:
        return Decimal(str(claimed)).quantize(MONEY_QUANTIZE) == actual.quantize(
            MONEY_QUANTIZE
        )
    except (ArithmeticError, ValueError):
        return False
