"""AI investigation tests (Prompt 6) — schema, grounding, safety, API.

All tests use a deterministic mock/stub provider; no external API is called.
"""

import pytest

from app.errors import AppError
from app.services import investigation_service as inv
from app.stores.data_store import store
from tests.conftest import upload

ALL_SOURCES = ["orders", "payments", "refunds", "fees", "settlements"]
EXC = "EXC-PAY002"  # AMOUNT_MISMATCH exception from the fixtures


def _prepare(client, fixture_bytes):
    for source in ALL_SOURCES:
        upload(client, source, f"{source}.csv", fixture_bytes(f"{source}.csv"))
    client.post("/api/v1/reconciliation/run")
    client.post("/api/v1/exceptions/generate")


def _valid(evidence=None, classification="OTHER", confidence=80, action="REVIEW"):
    return {
        "classification": classification,
        "summary": "A summary.",
        "root_cause": "A root cause.",
        "confidence": confidence,
        "evidence": evidence if evidence is not None else [{"source": "payments", "id": "PAY002"}],
        "missing_evidence": [],
        "recommended_action": action,
        "reason": "Because.",
    }


class StubProvider:
    name = "stub"
    model = "stub-model"

    def __init__(self, payload):
        self.payload = payload

    def investigate(self, bundle):
        return self.payload


class FailingProvider:
    name = "fail"
    model = "fail-model"

    def investigate(self, bundle):
        raise RuntimeError("provider exploded")


def _investigate(payload, exc_id=EXC):
    return inv.investigate(exc_id, provider=StubProvider(payload))


def _expect(payload, code, exc_id=EXC):
    with pytest.raises(AppError) as info:
        _investigate(payload, exc_id)
    assert info.value.code == code


# ---- Schema validation ----------------------------------------------------

def test_schema_missing_classification(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    payload = _valid()
    del payload["classification"]
    _expect(payload, "AI_VALIDATION_FAILED")


def test_schema_invalid_classification(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    _expect(_valid(classification="NONSENSE"), "AI_VALIDATION_FAILED")


def test_schema_confidence_below_zero(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    _expect(_valid(confidence=-5), "AI_VALIDATION_FAILED")


def test_schema_confidence_above_hundred(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    _expect(_valid(confidence=150), "AI_VALIDATION_FAILED")


def test_schema_invalid_action(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    _expect(_valid(action="DELETE_EVERYTHING"), "AI_VALIDATION_FAILED")


def test_schema_malformed_evidence(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    _expect(_valid(evidence=[{"source": "payments"}]), "AI_VALIDATION_FAILED")


# ---- Evidence grounding ---------------------------------------------------

def test_grounding_valid_reference_accepted(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    result = _investigate(_valid(classification="EXPECTED_FEE"))
    assert result["classification"] == "EXPECTED_FEE"


def test_grounding_nonexistent_payment_rejected(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    _expect(_valid(evidence=[{"source": "payments", "id": "PAY999"}]), "AI_GROUNDING_FAILED")


def test_grounding_incorrect_amount_rejected(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    _expect(
        _valid(evidence=[{"source": "payments", "id": "PAY002", "amount": "999999"}]),
        "AI_GROUNDING_FAILED",
    )


def test_grounding_invented_refund_rejected(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    _expect(_valid(evidence=[{"source": "refunds", "id": "REF-INVENTED"}]), "AI_GROUNDING_FAILED")


def test_grounding_unsupported_settlement_rejected(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    _expect(_valid(evidence=[{"source": "settlements", "id": "SET-NOPE"}]), "AI_GROUNDING_FAILED")


# ---- Safety rules ---------------------------------------------------------

def test_auto_resolve_high_confidence_stays_recommendation(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    result = _investigate(_valid(confidence=95, action="AUTO_RESOLVE"))
    assert result["recommended_action"] == "AUTO_RESOLVE"
    # Exception is NOT auto-resolved.
    assert store.get_exception(EXC)["status"] == "OPEN"


def test_auto_resolve_medium_confidence_downgraded_to_review(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    result = _investigate(_valid(confidence=72, action="AUTO_RESOLVE"))
    assert result["recommended_action"] == "REVIEW"


def test_low_confidence_forces_escalate(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    result = _investigate(_valid(confidence=40, action="AUTO_RESOLVE"))
    assert result["recommended_action"] == "ESCALATE"


def test_ai_cannot_change_financial_values(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    before = client.get(f"/api/v1/exceptions/{EXC}").json()
    client.post(f"/api/v1/exceptions/{EXC}/investigate")  # mock provider
    after = client.get(f"/api/v1/exceptions/{EXC}").json()
    for field in ("expected_amount", "actual_amount", "difference",
                  "potential_leakage", "affected_amount", "status"):
        assert before[field] == after[field]


def test_insufficient_evidence_reachable(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    # The mock returns INSUFFICIENT_EVIDENCE for an unexplained amount mismatch.
    result = client.post(f"/api/v1/exceptions/{EXC}/investigate").json()["investigation"]
    assert result["classification"] == "INSUFFICIENT_EVIDENCE"
    assert result["recommended_action"] == "ESCALATE"


# ---- Provider / response failures -----------------------------------------

def test_provider_failure_controlled_and_exception_unchanged(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    with pytest.raises(AppError) as info:
        inv.investigate(EXC, provider=FailingProvider())
    assert info.value.code == "AI_PROVIDER_ERROR"
    assert store.get_exception(EXC)["status"] == "OPEN"


def test_malformed_plaintext_response_rejected(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    _expect("this is not json at all", "AI_INVALID_RESPONSE")


# ---- API ------------------------------------------------------------------

def test_investigate_and_get_via_api(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    posted = client.post(f"/api/v1/exceptions/{EXC}/investigate")
    assert posted.status_code == 200
    got = client.get(f"/api/v1/exceptions/{EXC}/investigation")
    assert got.status_code == 200
    assert got.json()["investigation"]["exception_id"] == EXC


def test_get_investigation_none(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    resp = client.get(f"/api/v1/exceptions/{EXC}/investigation")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "INVESTIGATION_NOT_FOUND"


def test_investigate_missing_exception(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    resp = client.post("/api/v1/exceptions/EXC-NOPE/investigate")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "EXCEPTION_NOT_FOUND"


def test_investigate_without_reconciliation_evidence(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    store.set_reconciliation(None)  # drop reconciliation evidence
    resp = client.post(f"/api/v1/exceptions/{EXC}/investigate")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "RECONCILIATION_EVIDENCE_NOT_AVAILABLE"


def test_ground_truth_classifications(client, fixture_bytes):
    _prepare(client, fixture_bytes)
    expected = {
        "EXC-PAY003": "MISSING_SETTLEMENT",
        "EXC-PAY008": "ORDER_MAPPING_ERROR",
        "EXC-PAY002": "INSUFFICIENT_EVIDENCE",
        "EXC-SET999": "DATA_INTEGRITY_ISSUE",
    }
    for exc_id, classification in expected.items():
        result = client.post(f"/api/v1/exceptions/{exc_id}/investigate").json()["investigation"]
        assert result["classification"] == classification


def test_duplicate_transaction_classification():
    # Seed a duplicate-payment exception directly and investigate with the mock.
    store.reset()
    store.set_reconciliation({
        "run": {}, "summary": {},
        "results": [{
            "payment_id": "PAYD", "order_id": "ORDD", "status": "DUPLICATE_PAYMENT",
            "payment_amount": "1000.00", "expected_settlement": "1000.00",
            "actual_settlement": "1000.00", "difference": "0.00",
        }],
        "results_by_id": {"PAYD": {
            "payment_id": "PAYD", "order_id": "ORDD", "status": "DUPLICATE_PAYMENT",
            "payment_amount": "1000.00", "expected_settlement": "1000.00",
            "actual_settlement": "1000.00", "difference": "0.00",
        }},
        "orphans": {"settlements": [], "refunds": [], "fees": []},
    })
    from app.services import exception_service as es
    es.generate_exceptions()
    result = inv.investigate("EXC-PAYD")
    assert result["classification"] == "DUPLICATE_TRANSACTION"
