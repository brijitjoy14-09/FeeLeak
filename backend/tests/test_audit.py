"""Audit trail + Reject action tests (Prompt 8)."""

from tests.conftest import upload

ALL_SOURCES = ["orders", "payments", "refunds", "fees", "settlements"]


def _prepare(client, fixture_bytes):
    for s in ALL_SOURCES:
        upload(client, s, f"{s}.csv", fixture_bytes(f"{s}.csv"))
    client.post("/api/v1/reconciliation/run")
    client.post("/api/v1/exceptions/generate")


def test_reject_requires_reason(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    bad = client.patch("/api/v1/exceptions/EXC-PAY002/status", json={"status": "REJECTED"})
    assert bad.status_code == 422
    assert bad.json()["error"]["code"] == "REJECTION_REASON_REQUIRED"


def test_reject_sets_status_and_reason(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    ok = client.patch(
        "/api/v1/exceptions/EXC-FEE999/status",
        json={"status": "REJECTED", "note": "Known orphan, accepted as-is."},
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["status"] == "REJECTED"
    assert body["rejection_reason"] == "Known orphan, accepted as-is."


def test_audit_trail_records_lifecycle(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    client.patch("/api/v1/exceptions/EXC-PAY002/status", json={"status": "IN_REVIEW"})
    client.patch(
        "/api/v1/exceptions/EXC-PAY002/status",
        json={"status": "RESOLVED", "note": "Confirmed with processor."},
    )
    events = client.get("/api/v1/exceptions/EXC-PAY002/audit").json()["events"]
    types = [e["event_type"] for e in events]
    assert types == ["EXCEPTION_CREATED", "REVIEW_STARTED", "RESOLVED"]
    # who/what/when/why present on the resolution event.
    resolved = events[-1]
    assert resolved["actor"] == "finance-controller"
    assert resolved["reason"] == "Confirmed with processor."
    assert resolved["timestamp"]


def test_audit_investigation_event(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    client.post("/api/v1/exceptions/EXC-PAY003/investigate")
    events = client.get("/api/v1/exceptions/EXC-PAY003/audit").json()["events"]
    assert any(e["event_type"] == "AI_INVESTIGATION" for e in events)
    ai_event = next(e for e in events if e["event_type"] == "AI_INVESTIGATION")
    assert ai_event["actor"].startswith("ai:")


def test_analytics_reflects_human_decision(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    before = client.get("/api/v1/analytics/summary").json()
    client.patch("/api/v1/exceptions/EXC-PAY002/status", json={"status": "IN_REVIEW"})
    client.patch(
        "/api/v1/exceptions/EXC-PAY002/status",
        json={"status": "RESOLVED", "note": "done"},
    )
    after = client.get("/api/v1/analytics/summary").json()
    assert after["resolved_exceptions"] == before["resolved_exceptions"] + 1
    assert after["unresolved_exceptions"] == before["unresolved_exceptions"] - 1
