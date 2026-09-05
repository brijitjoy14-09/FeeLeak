"""Reconciliation engine tests: unit-level financial logic + ground-truth run."""

from decimal import Decimal

from app.config import RECONCILIATION_TOLERANCE
from app.services import reconciliation_service as rs
from app.stores.data_store import store
from tests.conftest import upload

ALL_SOURCES = ["orders", "payments", "refunds", "fees", "settlements"]


def _load_all(client, fixture_bytes):
    for source in ALL_SOURCES:
        upload(client, source, f"{source}.csv", fixture_bytes(f"{source}.csv"))


# ---- Unit tests on the engine internals -----------------------------------

def _payment(pid, oid, amount):
    return {"payment_id": pid, "order_id": oid, "payment_amount": Decimal(amount)}


def _seed(payments=None, orders=None, refunds=None, fees=None, settlements=None):
    def ds(records):
        return {"records": records, "columns": [], "record_count": len(records),
                "status": "loaded"}

    store.put_dataset("payments", ds(payments or []))
    store.put_dataset("orders", ds(orders or []))
    store.put_dataset("refunds", ds(refunds or []))
    store.put_dataset("fees", ds(fees or []))
    store.put_dataset("settlements", ds(settlements or []))


def test_perfect_match():
    _seed(
        payments=[_payment("PAY001", "ORD001", "10000")],
        orders=[{"order_id": "ORD001", "order_amount": Decimal("10000")}],
        refunds=[{"refund_id": "R1", "payment_id": "PAY001", "refund_amount": Decimal("1000")}],
        fees=[{"fee_id": "F1", "payment_id": "PAY001", "fee_amount": Decimal("200"), "tax_amount": Decimal("36")}],
        settlements=[{"settlement_id": "S1", "payment_id": "PAY001", "settlement_amount": Decimal("8764")}],
    )
    rs.run_reconciliation()
    r = rs.get_result("PAY001")
    assert r["expected_settlement"] == "8764.00"
    assert r["actual_settlement"] == "8764.00"
    assert r["difference"] == "0.00"
    assert r["status"] == "MATCHED"


def test_amount_mismatch():
    _seed(
        payments=[_payment("PAY001", "ORD001", "5500")],
        orders=[{"order_id": "ORD001", "order_amount": Decimal("5500")}],
        fees=[{"fee_id": "F", "payment_id": "PAY001", "fee_amount": Decimal("200"), "tax_amount": Decimal("36")}],
        settlements=[{"settlement_id": "S", "payment_id": "PAY001", "settlement_amount": Decimal("5000")}],
    )
    rs.run_reconciliation()
    r = rs.get_result("PAY001")
    assert r["difference"] == "264.00"
    assert r["status"] == "MISMATCH"


def test_missing_settlement():
    _seed(
        payments=[_payment("PAY001", "ORD001", "8000")],
        orders=[{"order_id": "ORD001", "order_amount": Decimal("8000")}],
    )
    rs.run_reconciliation()
    r = rs.get_result("PAY001")
    assert r["actual_settlement"] == "0.00"
    assert r["status"] == "MISSING_SETTLEMENT"


def test_multiple_refunds_and_fees_and_settlements():
    _seed(
        payments=[_payment("PAY001", "ORD001", "12000")],
        orders=[{"order_id": "ORD001", "order_amount": Decimal("12000")}],
        refunds=[
            {"refund_id": "R1", "payment_id": "PAY001", "refund_amount": Decimal("500")},
            {"refund_id": "R2", "payment_id": "PAY001", "refund_amount": Decimal("300")},
        ],
        fees=[
            {"fee_id": "F1", "payment_id": "PAY001", "fee_amount": Decimal("200"), "tax_amount": Decimal("36")},
            {"fee_id": "F2", "payment_id": "PAY001", "fee_amount": Decimal("50"), "tax_amount": Decimal("9")},
        ],
        settlements=[
            {"settlement_id": "S1", "payment_id": "PAY001", "settlement_amount": Decimal("5000")},
            {"settlement_id": "S2", "payment_id": "PAY001", "settlement_amount": Decimal("5905")},
        ],
    )
    rs.run_reconciliation()
    r = rs.get_result("PAY001")
    assert r["total_refund"] == "800.00"
    assert r["total_fee"] == "250.00"
    assert r["total_tax"] == "45.00"
    assert r["actual_settlement"] == "10905.00"
    assert r["status"] == "MATCHED"


def test_missing_order():
    _seed(
        payments=[_payment("PAY001", "ORD999", "6000")],
        orders=[{"order_id": "ORD001", "order_amount": Decimal("10000")}],
        settlements=[{"settlement_id": "S", "payment_id": "PAY001", "settlement_amount": Decimal("6000")}],
    )
    rs.run_reconciliation()
    assert rs.get_result("PAY001")["status"] == "ORDER_NOT_FOUND"


def test_orphans_detected():
    _seed(
        payments=[_payment("PAY001", "ORD001", "1000")],
        orders=[{"order_id": "ORD001", "order_amount": Decimal("1000")}],
        refunds=[{"refund_id": "R", "payment_id": "PAYX", "refund_amount": Decimal("10")}],
        fees=[{"fee_id": "F", "payment_id": "PAYX", "fee_amount": Decimal("5"), "tax_amount": Decimal("1")}],
        settlements=[
            {"settlement_id": "S1", "payment_id": "PAY001", "settlement_amount": Decimal("1000")},
            {"settlement_id": "S2", "payment_id": "PAYY", "settlement_amount": Decimal("99")},
        ],
    )
    out = rs.run_reconciliation()
    assert out["summary"]["orphan_records"] == {"settlements": 1, "refunds": 1, "fees": 1}


def test_duplicate_payment_id():
    _seed(
        payments=[_payment("PAY001", "ORD001", "1000"), _payment("PAY001", "ORD001", "1000")],
        orders=[{"order_id": "ORD001", "order_amount": Decimal("1000")}],
        settlements=[{"settlement_id": "S", "payment_id": "PAY001", "settlement_amount": Decimal("1000")}],
    )
    rs.run_reconciliation()
    assert rs.get_result("PAY001")["status"] == "DUPLICATE_PAYMENT"


def test_decimal_precision_no_float_artifacts():
    _seed(
        payments=[_payment("PAY001", "ORD001", "100.10")],
        orders=[{"order_id": "ORD001", "order_amount": Decimal("100.10")}],
        fees=[{"fee_id": "F", "payment_id": "PAY001", "fee_amount": Decimal("0.10"), "tax_amount": Decimal("0")}],
        settlements=[{"settlement_id": "S", "payment_id": "PAY001", "settlement_amount": Decimal("100.00")}],
    )
    rs.run_reconciliation()
    r = rs.get_result("PAY001")
    assert r["expected_settlement"] == "100.00"
    assert r["difference"] == "0.00"
    assert r["status"] == "MATCHED"


def test_tolerance_boundary():
    # 0.01 within tolerance -> MATCHED
    _seed(
        payments=[_payment("PAY001", "ORD001", "100.00")],
        orders=[{"order_id": "ORD001", "order_amount": Decimal("100.00")}],
        settlements=[{"settlement_id": "S", "payment_id": "PAY001", "settlement_amount": Decimal("99.99")}],
    )
    rs.run_reconciliation()
    assert abs(RECONCILIATION_TOLERANCE) == Decimal("0.01")
    assert rs.get_result("PAY001")["status"] == "MATCHED"

    # 0.02 outside tolerance -> MISMATCH
    _seed(
        payments=[_payment("PAY002", "ORD001", "100.00")],
        orders=[{"order_id": "ORD001", "order_amount": Decimal("100.00")}],
        settlements=[{"settlement_id": "S", "payment_id": "PAY002", "settlement_amount": Decimal("99.98")}],
    )
    rs.run_reconciliation()
    assert rs.get_result("PAY002")["status"] == "MISMATCH"


def test_idempotency():
    _seed(
        payments=[_payment("PAY001", "ORD001", "1000")],
        orders=[{"order_id": "ORD001", "order_amount": Decimal("1000")}],
        settlements=[{"settlement_id": "S", "payment_id": "PAY001", "settlement_amount": Decimal("1000")}],
    )
    first = rs.run_reconciliation()["summary"]
    second = rs.run_reconciliation()["summary"]
    assert first == second
    assert len(rs.get_results()) == 1  # not duplicated across runs


# ---- API + ground-truth integration ---------------------------------------

def test_run_missing_datasets(client, fixture_bytes):
    upload(client, "payments", "payments.csv", fixture_bytes("payments.csv"))
    resp = client.post("/api/v1/reconciliation/run")
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "MISSING_DATASET"
    assert "orders" in body["error"]["details"]["missing_sources"]


def test_full_run_ground_truth(client, fixture_bytes):
    _load_all(client, fixture_bytes)
    resp = client.post("/api/v1/reconciliation/run")
    assert resp.status_code == 200
    summary = resp.json()["summary"]

    # Deterministic ground truth for the fixture dataset (8 payments).
    assert summary["total_payments"] == 8
    assert summary["matched"] == 4
    assert summary["mismatched"] == 2
    assert summary["missing_settlement"] == 1
    assert summary["order_not_found"] == 1
    assert summary["duplicate_payment"] == 0
    assert summary["orphan_records"] == {"settlements": 1, "refunds": 1, "fees": 1}

    # Spot-check individual results via the API.
    r1 = client.get("/api/v1/reconciliation/results/PAY001").json()
    assert r1["status"] == "MATCHED"
    assert r1["expected_settlement"] == "8764.00"

    r2 = client.get("/api/v1/reconciliation/results/PAY002").json()
    assert r2["status"] == "MISMATCH"
    assert r2["difference"] == "264.00"

    # Filtering.
    mismatches = client.get("/api/v1/reconciliation/results?status=MISMATCH").json()
    assert mismatches["returned"] == 2
