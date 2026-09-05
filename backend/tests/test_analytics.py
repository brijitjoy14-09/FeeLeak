"""Analytics + risk prioritization tests (Prompt 9) — deterministic."""

from decimal import Decimal

import pytest

from app.errors import AppError
from app.services import analytics_service as an
from app.services import exception_service as es
from app.stores.data_store import store


def _result(pid, status, payment, expected, actual, order_id="ORD1"):
    diff = Decimal(expected) - Decimal(actual)
    return {
        "payment_id": pid, "order_id": order_id, "status": status,
        "payment_amount": f"{Decimal(payment):.2f}",
        "expected_settlement": f"{Decimal(expected):.2f}",
        "actual_settlement": f"{Decimal(actual):.2f}",
        "difference": f"{diff:.2f}",
    }


def _seed(results, orphans=None, summary=None, payments=None):
    store.reset()
    if payments is not None:
        store.put_dataset("payments", {
            "records": payments, "columns": [], "record_count": len(payments),
            "status": "loaded",
        })
    store.set_reconciliation({
        "run": {}, "summary": summary or {"total_payments": len(results), "matched": 0},
        "results": results, "results_by_id": {r["payment_id"]: r for r in results},
        "orphans": orphans or {"settlements": [], "refunds": [], "fees": []},
    })
    es.generate_exceptions()


# ---- Summary rates --------------------------------------------------------

def test_match_and_exception_rate():
    results = [_result(f"P{i}", "MISMATCH", "100", "100", "50") for i in range(10)]
    _seed(results, summary={"total_payments": 100, "matched": 90})
    s = an.get_summary()
    assert s["match_rate"] == 90.0
    assert s["exception_rate"] == 10.0
    assert s["total_exceptions"] == 10


def test_potential_leakage_sum():
    results = [
        _result("P1", "MISSING_SETTLEMENT", "5000", "5000", "0"),
        _result("P2", "MISSING_SETTLEMENT", "3000", "3000", "0"),
        _result("P3", "MISSING_SETTLEMENT", "2000", "2000", "0"),
    ]
    _seed(results, summary={"total_payments": 3, "matched": 0})
    assert an.get_summary()["potential_leakage"] == "10000.00"


def test_resolution_rate():
    results = [_result(f"P{i}", "MISSING_SETTLEMENT", "1000", "1000", "0") for i in range(10)]
    _seed(results, summary={"total_payments": 10, "matched": 0})
    ids = [e["exception_id"] for e in es.list_exceptions()]
    for i in range(6):
        es.update_status(ids[i], "IN_REVIEW")
        es.update_status(ids[i], "RESOLVED", note="done")
    es.update_status(ids[6], "ESCALATED", note="escalate")
    es.update_status(ids[7], "ESCALATED", note="escalate")
    es.update_status(ids[8], "IN_REVIEW")
    # ids[9] stays OPEN
    assert an.get_summary()["resolution_rate"] == 60.0


def test_zero_exceptions_no_divide_by_zero():
    _seed([], summary={"total_payments": 100, "matched": 100})
    s = an.get_summary()
    assert s["exception_rate"] == 0.0
    assert s["potential_leakage"] == "0.00"
    assert s["resolution_rate"] == 0.0


# ---- Distribution ---------------------------------------------------------

def test_exception_distribution_counts_and_amounts():
    results = [
        _result("P1", "MISSING_SETTLEMENT", "2000", "2000", "0"),
        _result("P2", "MISSING_SETTLEMENT", "2000", "2000", "0"),
        _result("P3", "MISSING_SETTLEMENT", "2000", "2000", "0"),
        _result("P4", "MISMATCH", "5000", "5000", "4000"),  # affected 1000
        _result("P5", "MISMATCH", "5000", "5000", "4000"),  # affected 1000
    ]
    _seed(results, summary={"total_payments": 5, "matched": 0})
    dist = {d["classification"]: d for d in an.get_exception_distribution()["data"]}
    assert dist["MISSING_SETTLEMENT"]["count"] == 3
    assert dist["MISSING_SETTLEMENT"]["amount"] == "6000.00"
    assert dist["AMOUNT_MISMATCH"]["count"] == 2
    assert dist["AMOUNT_MISMATCH"]["amount"] == "2000.00"
    # Ranked by financial impact.
    assert an.get_exception_distribution()["data"][0]["classification"] == "MISSING_SETTLEMENT"


# ---- Risk -----------------------------------------------------------------

def test_risk_score_deterministic_and_anchored():
    a = es.compute_risk(Decimal("25000"), "HIGH", 0, "OPEN")
    b = es.compute_risk(Decimal("25000"), "HIGH", 0, "OPEN")
    assert a == b
    score, level, _ = a
    assert score == 75 and level == "CRITICAL"


def test_risk_ordering_by_score_then_amount():
    results = [
        _result("PBIG", "MISSING_SETTLEMENT", "40000", "40000", "0"),   # huge -> top
        _result("PSMALL", "MISMATCH", "600", "600", "300"),             # small
        _result("PMID", "MISSING_SETTLEMENT", "6000", "6000", "0"),     # mid
    ]
    _seed(results, summary={"total_payments": 3, "matched": 0})
    order = [d["exception_id"] for d in an.get_risk_priorities()["data"]]
    assert order[0] == "EXC-PBIG"
    assert order.index("EXC-PMID") < order.index("EXC-PSMALL")


def test_risk_tie_broken_by_amount():
    # Both amounts exceed the risk cap -> equal amount_score -> equal risk;
    # tie-break by discrepancy amount descending.
    results = [
        _result("PA", "MISSING_SETTLEMENT", "30000", "30000", "0"),
        _result("PB", "MISSING_SETTLEMENT", "26000", "26000", "0"),
    ]
    _seed(results, summary={"total_payments": 2, "matched": 0})
    data = an.get_risk_priorities()["data"]
    assert data[0]["risk_score"] == data[1]["risk_score"]
    assert data[0]["exception_id"] == "EXC-PA"  # larger discrepancy first


def test_risk_priorities_limit_validation():
    _seed([_result("P1", "MISSING_SETTLEMENT", "1000", "1000", "0")],
          summary={"total_payments": 1, "matched": 0})
    with pytest.raises(AppError) as info:
        an.get_risk_priorities(limit=9999)
    assert info.value.code == "INVALID_LIMIT"


# ---- Filters --------------------------------------------------------------

def test_status_filter_excludes_resolved():
    results = [_result(f"P{i}", "MISSING_SETTLEMENT", "1000", "1000", "0") for i in range(3)]
    _seed(results, summary={"total_payments": 3, "matched": 0})
    ids = [e["exception_id"] for e in es.list_exceptions()]
    es.update_status(ids[0], "IN_REVIEW")
    es.update_status(ids[0], "RESOLVED", note="x")
    open_summary = an.get_summary(status="OPEN")
    assert open_summary["total_exceptions"] == 2  # resolved one excluded


def test_classification_filter():
    results = [
        _result("P1", "MISSING_SETTLEMENT", "1000", "1000", "0"),
        _result("P2", "MISMATCH", "5000", "5000", "4000"),
    ]
    _seed(results, summary={"total_payments": 2, "matched": 0})
    s = an.get_summary(classification="MISSING_SETTLEMENT")
    assert s["total_exceptions"] == 1


def test_invalid_date_range_rejected():
    _seed([_result("P1", "MISSING_SETTLEMENT", "1000", "1000", "0")],
          summary={"total_payments": 1, "matched": 0})
    with pytest.raises(AppError) as info:
        an.get_summary(start_date="2026-08-25", end_date="2026-08-20")
    assert info.value.code == "INVALID_DATE_RANGE"


def test_date_filter_selects_range():
    payments = [
        {"payment_id": "P1", "payment_date": "2026-08-01", "payment_amount": Decimal("1000")},
        {"payment_id": "P2", "payment_date": "2026-08-10", "payment_amount": Decimal("1000")},
    ]
    results = [
        _result("P1", "MISSING_SETTLEMENT", "1000", "1000", "0"),
        _result("P2", "MISSING_SETTLEMENT", "1000", "1000", "0"),
    ]
    _seed(results, summary={"total_payments": 2, "matched": 0}, payments=payments)
    s = an.get_summary(start_date="2026-08-05", end_date="2026-08-15")
    assert s["total_exceptions"] == 1


# ---- Leakage trend --------------------------------------------------------

def test_leakage_trend_unavailable_without_dates():
    # No payments dataset -> no dates -> controlled unavailable response.
    _seed([_result("P1", "MISSING_SETTLEMENT", "1000", "1000", "0")],
          summary={"total_payments": 1, "matched": 0})
    trend = an.get_leakage_trend()
    assert trend["available"] is False
    assert trend["data"] == []


def test_leakage_trend_daily_with_dates():
    payments = [
        {"payment_id": "P1", "payment_date": "2026-08-01", "payment_amount": Decimal("1000")},
        {"payment_id": "P2", "payment_date": "2026-08-02", "payment_amount": Decimal("1000")},
    ]
    results = [
        _result("P1", "MISSING_SETTLEMENT", "5000", "5000", "0"),
        _result("P2", "MISSING_SETTLEMENT", "3000", "3000", "0"),
    ]
    _seed(results, summary={"total_payments": 2, "matched": 0}, payments=payments)
    trend = an.get_leakage_trend()
    assert trend["available"] is True
    assert trend["data"] == [
        {"date": "2026-08-01", "potential_leakage": "5000.00"},
        {"date": "2026-08-02", "potential_leakage": "3000.00"},
    ]
