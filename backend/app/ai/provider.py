"""AI investigation provider abstraction + a deterministic mock (Prompt 6).

The application never couples to a specific LLM vendor. Providers accept an
evidence bundle and return a RAW dict (the service validates it). The mock is
fully deterministic so all tests run without any external API or credentials.
"""

from ..config import AI_PROVIDER
from ..errors import AppError


class AIInvestigationProvider:
    """Base provider interface."""

    name = "base"
    model = "base"

    def investigate(self, bundle: dict) -> dict:  # pragma: no cover - interface
        raise NotImplementedError

    def generate_insight(self, metrics: dict) -> dict:  # pragma: no cover
        """Produce an executive summary from validated metrics only."""
        raise NotImplementedError


def _grounded_evidence(bundle):
    """Cite exactly the records present in the bundle (always grounded)."""
    evidence = []
    if bundle.get("payment"):
        p = bundle["payment"]
        evidence.append(
            {"source": "payments", "id": p.get("payment_id"),
             "amount": p.get("payment_amount")}
        )
    for r in bundle.get("refunds", []):
        evidence.append(
            {"source": "refunds", "id": r.get("refund_id"),
             "amount": r.get("refund_amount")}
        )
    for f in bundle.get("fees", []):
        evidence.append(
            {"source": "fees", "id": f.get("fee_id"),
             "amount": f.get("fee_amount")}
        )
    for s in bundle.get("settlements", []):
        evidence.append(
            {"source": "settlements", "id": s.get("settlement_id"),
             "amount": s.get("settlement_amount")}
        )
    if bundle.get("orphan_record"):
        rec = bundle["orphan_record"]
        exc_type = bundle["exception"]["type"]
        src, idf, amtf = {
            "ORPHAN_SETTLEMENT": ("settlements", "settlement_id", "settlement_amount"),
            "ORPHAN_REFUND": ("refunds", "refund_id", "refund_amount"),
            "ORPHAN_FEE": ("fees", "fee_id", "fee_amount"),
        }[exc_type]
        evidence.append({"source": src, "id": rec.get(idf), "amount": rec.get(amtf)})
    return evidence


class MockAIInvestigationProvider(AIInvestigationProvider):
    """Deterministic, evidence-grounded mock investigator."""

    name = "mock"
    model = "mock-model"

    def investigate(self, bundle: dict) -> dict:
        exc = bundle["exception"]
        exc_type = exc["type"]
        payment_id = exc.get("payment_id")
        evidence = _grounded_evidence(bundle)

        if exc_type == "MISSING_SETTLEMENT":
            return {
                "classification": "MISSING_SETTLEMENT",
                "summary": (
                    f"No settlement record was found for payment {payment_id}; "
                    f"the full expected amount is unsettled."
                ),
                "root_cause": "The settlement for this payment is absent from the settlements dataset.",
                "confidence": 80,
                "evidence": evidence,
                "missing_evidence": [
                    f"No settlement record references payment {payment_id}.",
                ],
                "recommended_action": "REVIEW",
                "reason": "A settlement may be delayed or missing; a human should confirm.",
            }

        if exc_type == "ORDER_NOT_FOUND":
            return {
                "classification": "ORDER_MAPPING_ERROR",
                "summary": (
                    f"Payment {payment_id} references order {exc.get('order_id')} "
                    f"which is not present in the orders dataset."
                ),
                "root_cause": "The payment's order_id does not map to any known order.",
                "confidence": 85,
                "evidence": evidence,
                "missing_evidence": [
                    f"Order {exc.get('order_id')} is absent from the orders dataset.",
                ],
                "recommended_action": "REVIEW",
                "reason": "Likely a data-mapping issue; verify the order reference.",
            }

        if exc_type == "DUPLICATE_PAYMENT":
            return {
                "classification": "DUPLICATE_TRANSACTION",
                "summary": f"Payment identifier {payment_id} appears more than once.",
                "root_cause": "Duplicate payment identifier detected across payment records.",
                "confidence": 88,
                "evidence": evidence,
                "missing_evidence": [],
                "recommended_action": "REVIEW",
                "reason": "Duplicate identifiers need human confirmation before any action.",
            }

        if exc_type in ("ORPHAN_SETTLEMENT", "ORPHAN_REFUND", "ORPHAN_FEE"):
            return {
                "classification": "DATA_INTEGRITY_ISSUE",
                "summary": (
                    f"{exc_type.replace('ORPHAN_', '').title()} record "
                    f"{exc.get('record_id')} references a payment that does not exist."
                ),
                "root_cause": "The referenced payment is missing from the payments dataset.",
                "confidence": 82,
                "evidence": evidence,
                "missing_evidence": [
                    f"Payment {exc.get('payment_id')} is absent from the payments dataset.",
                ],
                "recommended_action": "REVIEW",
                "reason": "Orphan records indicate a data-integrity gap to reconcile.",
            }

        # AMOUNT_MISMATCH and anything else: the residual is unexplained.
        diff = exc.get("difference")
        return {
            "classification": "INSUFFICIENT_EVIDENCE",
            "summary": (
                f"The settlement for payment {payment_id} differs from expected and "
                f"no supplied record explains the residual of {diff}."
            ),
            "root_cause": "No fee, refund, or adjustment in the evidence accounts for the difference.",
            "confidence": 60,
            "evidence": evidence,
            "missing_evidence": [
                f"No adjustment record explains the remaining difference of {diff}.",
            ],
            "recommended_action": "ESCALATE",
            "reason": "The discrepancy is unexplained by available evidence.",
        }


    def generate_insight(self, metrics: dict) -> dict:
        """Deterministic executive summary using ONLY the supplied metrics.

        Never invents numbers: every figure is taken verbatim from `metrics`
        (which the insight service pre-formats and validates).
        """
        s = metrics["summary"]
        distribution = metrics.get("distribution", [])
        risks = metrics.get("risk_priorities", [])
        leakage_display = metrics.get("potential_leakage_display", s["potential_leakage"])
        critical = metrics.get("critical_count", 0)
        top = distribution[0] if distribution else None

        findings = []
        if top:
            findings.append(
                f"Largest financial impact: {top['classification']} "
                f"({metrics.get('top_amount_display', top['amount'])} across "
                f"{top['count']} exception(s))."
            )
        findings.append(
            f"Resolution rate is {s['resolution_rate']}% "
            f"({s['resolved_exceptions']} of {s['total_exceptions']} resolved)."
        )
        if risks:
            r = risks[0]
            findings.append(
                f"Highest-risk exception is {r['exception_id']} "
                f"(risk {r['risk_score']}, {r['classification']})."
            )

        summary = (
            f"{s['transactions_processed']} transactions processed at a "
            f"{s['match_rate']}% match rate. {s['unresolved_exceptions']} exception(s) "
            f"remain active with {leakage_display} in potential unexplained leakage. "
            f"{critical} exception(s) are at critical risk and should be reviewed first."
        )
        return {
            "summary": summary,
            "key_findings": findings,
            "priority_exceptions": [r["exception_id"] for r in risks[:3]],
        }


def get_provider(name: str = None) -> AIInvestigationProvider:
    """Resolve a provider from config/env. Only 'mock' ships in this MVP."""
    provider_name = (name or AI_PROVIDER or "mock").lower()
    if provider_name == "mock":
        return MockAIInvestigationProvider()
    # A real provider (e.g. Anthropic) would be constructed here from env-based
    # credentials. Not configured in this MVP.
    raise AppError(
        "AI_PROVIDER_NOT_CONFIGURED",
        f"AI provider '{provider_name}' is not configured.",
        503,
        {"provider": provider_name},
    )
