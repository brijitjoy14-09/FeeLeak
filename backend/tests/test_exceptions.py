"""Exception management tests (Prompt 5) — deterministic detection + workflow."""

from decimal import Decimal

from app.services import exception_service as es
from app.stores.data_store import store
from tests.conftest import upload

ALL_SOURCES = ["orders", "payments", "refunds", "fees", "settlements"]


def _load_and_reconcile(client, fixture_bytes):
    for source in ALL_SOURCES:
        upload(client, source, f"{source}.csv", fixture_bytes(f"{source}.csv"))
    client.post("/api/v1/reconciliation/run")


def _result(payment_id, status, payment_amount, expected, actual, order_id="ORD1"):
    diff = Decimal(expected) - Decimal(actual)
    return {
        "payment_id": payment_id,
        "order_id": order_id,
        "status": status,
        "payment_amount": f"{Decimal(payment_amount):.2f}",
        "expected_settlement": f"{Decimal(expected):.2f}",
        "actual_settlement": f"{Decimal(actual):.2f}",
        "difference": f"{diff:.2f}",
    }


def _set_recon(results, orphans=None):
    store.set_reconciliation(
        {
            "run": {"run_id": "RUN-TEST", "status": "completed"},
            "summary": {},
            "results": results,
            "results_by_id": {r["payment_id"]: r for r in results},
            "orphans": orphans or {"settlements": [], "refunds": [], "fees": []},
        }
    )


# ---- Detection ------------------------------------------------------------

def test_matched_creates_no_exception():
    _set_recon([_result("PAY1", "MATCHED", "1000", "1000", "1000")])
    es.generate_exceptions()
    assert es.count_all() == 0


def test_detection_types_from_fixtures(client, fixture_bytes):
    _load_and_reconcile(client, fixture_bytes)
    client.post("/api/v1/exceptions/generate")
    by_id = {e["exception_id"]: e for e in
             client.get("/api/v1/exceptions?limit=100").json()["exceptions"]}
    assert by_id["EXC-PAY002"]["type"] == "AMOUNT_MISMATCH"
    assert by_id["EXC-PAY003"]["type"] == "MISSING_SETTLEMENT"
    assert by_id["EXC-PAY008"]["type"] == "ORDER_NOT_FOUND"
    assert by_id["EXC-SET999"]["type"] == "ORPHAN_SETTLEMENT"
    assert by_id["EXC-REF999"]["type"] == "ORPHAN_REFUND"
    assert by_id["EXC-FEE999"]["type"] == "ORPHAN_FEE"
    # 4 matched payments produce no exceptions.
    assert "EXC-PAY001" not in by_id


def test_duplicate_payment_detection():
    _set_recon([_result("PAYDUP", "DUPLICATE_PAYMENT", "1000", "1000", "1000")])
    es.generate_exceptions()
    exc = es.get_exception("EXC-PAYDUP")
    assert exc["type"] == "DUPLICATE_PAYMENT"


# ---- Leakage & affected amount --------------------------------------------

def test_leakage_positive_difference():
    _set_recon([_result("P", "MISMATCH", "10000", "10000", "9500")])
    es.generate_exceptions()
    exc = es.get_exception("EXC-P")
    assert exc["potential_leakage"] == "500.00"
    assert exc["affected_amount"] == "500.00"


def test_leakage_zero_when_merchant_favorable():
    _set_recon([_result("P", "MISMATCH", "10000", "10000", "10500")])
    es.generate_exceptions()
    exc = es.get_exception("EXC-P")
    assert exc["potential_leakage"] == "0.00"
    assert exc["difference"] == "-500.00"


def test_missing_settlement_leakage_equals_expected():
    _set_recon([_result("P", "MISSING_SETTLEMENT", "8500", "8500", "0")])
    es.generate_exceptions()
    exc = es.get_exception("EXC-P")
    assert exc["potential_leakage"] == "8500.00"
    assert exc["affected_amount"] == "8500.00"


def test_orphan_settlement_leakage_zero_affected_equals_amount():
    _set_recon(
        [],
        orphans={
            "settlements": [{"id": "SETX", "payment_id": "PZ", "amount": "1200.00", "kind": "settlement"}],
            "refunds": [],
            "fees": [],
        },
    )
    es.generate_exceptions()
    exc = es.get_exception("EXC-SETX")
    assert exc["potential_leakage"] == "0.00"
    assert exc["affected_amount"] == "1200.00"


# ---- Severity boundaries --------------------------------------------------

def test_severity_boundaries():
    cases = {
        "499.99": "LOW",
        "500": "MEDIUM",
        "4999.99": "MEDIUM",
        "5000": "HIGH",
        "24999.99": "HIGH",
        "25000": "CRITICAL",
    }
    for amount, level in cases.items():
        assert es.compute_severity(Decimal(amount)) == level


# ---- Priority -------------------------------------------------------------

def test_priority_orders_high_impact_first():
    _set_recon(
        [
            _result("PLOW", "MISMATCH", "300", "300", "100"),        # leak 200 LOW
            _result("PBIG", "MISSING_SETTLEMENT", "40000", "40000", "0"),  # 40000 CRITICAL
            _result("PMID", "MISMATCH", "6000", "6000", "0"),        # leak 6000 HIGH
        ]
    )
    es.generate_exceptions()
    ordered = [e["exception_id"] for e in es.list_exceptions()]
    assert ordered[0] == "EXC-PBIG"
    assert ordered.index("EXC-PMID") < ordered.index("EXC-PLOW")


# ---- Idempotency ----------------------------------------------------------

def test_idempotent_generation(client, fixture_bytes):
    _load_and_reconcile(client, fixture_bytes)
    first = client.post("/api/v1/exceptions/generate").json()["summary"]
    ids_first = sorted(e["exception_id"] for e in
                       client.get("/api/v1/exceptions?limit=100").json()["exceptions"])
    second = client.post("/api/v1/exceptions/generate").json()["summary"]
    ids_second = sorted(e["exception_id"] for e in
                        client.get("/api/v1/exceptions?limit=100").json()["exceptions"])
    assert first == second
    assert ids_first == ids_second
    assert len(ids_first) == len(set(ids_first))  # no duplicates


# ---- Workflow -------------------------------------------------------------

def _one_open(client):
    return client.get("/api/v1/exceptions?limit=1").json()["exceptions"][0]["exception_id"]


def test_generate_requires_reconciliation(client):
    resp = client.post("/api/v1/exceptions/generate")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "RECONCILIATION_NOT_RUN"


def test_valid_transition_and_resolution(client, fixture_bytes):
    _load_and_reconcile(client, fixture_bytes)
    client.post("/api/v1/exceptions/generate")
    exc_id = _one_open(client)

    started = client.patch(f"/api/v1/exceptions/{exc_id}/status", json={"status": "IN_REVIEW"})
    assert started.status_code == 200
    assert started.json()["status"] == "IN_REVIEW"

    # Resolving without a note fails.
    bad = client.patch(f"/api/v1/exceptions/{exc_id}/status", json={"status": "RESOLVED"})
    assert bad.status_code == 422
    assert bad.json()["error"]["code"] == "RESOLUTION_REQUIRED"

    ok = client.patch(
        f"/api/v1/exceptions/{exc_id}/status",
        json={"status": "RESOLVED", "note": "Fee difference confirmed with processor."},
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["status"] == "RESOLVED"
    assert body["resolution"]
    assert body["reviewed_by"] == "finance-controller"
    assert body["reviewed_at"]


def test_invalid_transition_rejected(client, fixture_bytes):
    _load_and_reconcile(client, fixture_bytes)
    client.post("/api/v1/exceptions/generate")
    exc_id = _one_open(client)
    resp = client.patch(f"/api/v1/exceptions/{exc_id}/status", json={"status": "RESOLVED"})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_TRANSITION"


def test_escalation_requires_reason(client, fixture_bytes):
    _load_and_reconcile(client, fixture_bytes)
    client.post("/api/v1/exceptions/generate")
    exc_id = _one_open(client)
    bad = client.patch(f"/api/v1/exceptions/{exc_id}/status", json={"status": "ESCALATED"})
    assert bad.status_code == 422
    assert bad.json()["error"]["code"] == "ESCALATION_REASON_REQUIRED"
    ok = client.patch(
        f"/api/v1/exceptions/{exc_id}/status",
        json={"status": "ESCALATED", "note": "Needs finance-lead sign-off."},
    )
    assert ok.status_code == 200
    assert ok.json()["escalation_reason"]


def test_unknown_exception_and_status(client, fixture_bytes):
    _load_and_reconcile(client, fixture_bytes)
    client.post("/api/v1/exceptions/generate")
    assert client.get("/api/v1/exceptions/EXC-NOPE").status_code == 404
    exc_id = _one_open(client)
    resp = client.patch(f"/api/v1/exceptions/{exc_id}/status", json={"status": "WAT"})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_STATUS"


def test_summary_excludes_resolved_from_active_kpis(client, fixture_bytes):
    _load_and_reconcile(client, fixture_bytes)
    client.post("/api/v1/exceptions/generate")
    exc_id = _one_open(client)
    client.patch(f"/api/v1/exceptions/{exc_id}/status", json={"status": "IN_REVIEW"})
    client.patch(f"/api/v1/exceptions/{exc_id}/status",
                 json={"status": "RESOLVED", "note": "Resolved for test."})
    summary = client.get("/api/v1/exceptions/summary").json()
    assert summary["resolved"] == 1
    assert summary["active_exceptions"] == summary["total_exceptions"] - 1
