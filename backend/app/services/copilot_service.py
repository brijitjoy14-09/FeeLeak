"""Finance Controller Copilot (Prompt 7).

A controlled decision-support interface. It maps a natural-language question to
ONE controlled intent, calls only registered READ-ONLY backend tools, and
composes the answer deterministically from those tool results — so every number
in the answer originates from the deterministic backend, never the LLM. The
Copilot cannot mutate anything (no resolve/escalate/reject, no SQL, no
unregistered functions).
"""

import re

from ..formatting import format_inr
from . import analytics_service, exception_service, investigation_service

_EXC_ID_RE = re.compile(r"\bEXC-[A-Za-z0-9]+\b", re.IGNORECASE)


# ---- Registered read-only tools (the ONLY functions the Copilot may call) --
TOOL_REGISTRY = {
    "get_exception": lambda exception_id: exception_service.get_exception(exception_id),
    "get_investigation": lambda exception_id: investigation_service
    .get_latest_investigation(exception_id),
    "get_analytics_summary": lambda: analytics_service.get_summary(),
    "get_leakage_trend": lambda: analytics_service.get_leakage_trend(),
    "get_exception_financial_impact": lambda: analytics_service
    .get_exception_distribution(),
    "get_risk_priorities": lambda limit=5: analytics_service.get_risk_priorities(limit=limit),
    "get_resolution_performance": lambda: analytics_service.get_resolution_performance(),
}


def _call_tool(name, *args, **kwargs):
    if name not in TOOL_REGISTRY:
        raise KeyError(f"unregistered tool: {name}")
    return TOOL_REGISTRY[name](*args, **kwargs)


def detect_intent(message: str):
    """Deterministic keyword-based intent detection. Returns (intent, exc_id)."""
    text = message.lower()
    exc_match = _EXC_ID_RE.search(message)
    exc_id = exc_match.group(0).upper() if exc_match else None

    if exc_id:
        if "why" in text or "explain" in text:
            return "EXCEPTION_EXPLANATION", exc_id
        return "EXCEPTION_INVESTIGATION", exc_id
    if any(k in text for k in ("investigate first", "priorit", "highest risk", "riskiest")):
        return "RISK_PRIORITIES", None
    if "leakage" in text and any(k in text for k in ("trend", "over time", "increasing", "daily")):
        return "LEAKAGE_TREND", None
    if any(k in text for k in ("impact", "category", "categories", "classification", "biggest")):
        return "FINANCIAL_IMPACT", None
    if any(k in text for k in ("resolution rate", "resolved", "performance", "throughput")):
        return "RESOLUTION_PERFORMANCE", None
    return "ANALYTICS_SUMMARY", None


def _answer_summary(s):
    return (
        f"Across {s['transactions_processed']} transactions, {s['match_rate']}% matched. "
        f"There are {s['unresolved_exceptions']} active exception(s) with "
        f"{format_inr(s['potential_leakage'])} in potential unexplained leakage. "
        f"The resolution rate is {s['resolution_rate']}%."
    )


def _answer_risk(risks):
    if not risks:
        return "There are no active exceptions to prioritize right now."
    lines = ["The highest-priority exceptions to investigate first are:"]
    for i, r in enumerate(risks, 1):
        lines.append(
            f"{i}. {r['exception_id']} — {format_inr(r['discrepancy'])} — "
            f"risk {r['risk_score']} ({r['risk_level']}, {r['classification']})"
        )
    top = risks[0]
    lines.append(
        f"Start with {top['exception_id']}: it combines the largest discrepancy "
        f"with {top['severity']} severity and unresolved status."
    )
    return "\n".join(lines)


def _answer_impact(data):
    if not data:
        return "No exceptions with financial impact were found."
    lines = ["Financial impact by exception category (largest first):"]
    for i, d in enumerate(data, 1):
        lines.append(
            f"{i}. {d['classification']} — {format_inr(d['amount'])} "
            f"({d['count']} exception(s))"
        )
    return "\n".join(lines)


def _answer_leakage_trend(trend):
    if not trend.get("available"):
        return trend.get("message", "Leakage trend data is unavailable.")
    points = trend["data"]
    lines = ["Potential leakage by day:"]
    for p in points:
        lines.append(f"{p['date']}: {format_inr(p['potential_leakage'])}")
    first = float(points[0]["potential_leakage"])
    last = float(points[-1]["potential_leakage"])
    direction = "increasing" if last > first else "decreasing" if last < first else "stable"
    lines.append(f"The trend is {direction} across the observed period.")
    return "\n".join(lines)


def _answer_resolution(perf):
    return (
        f"Resolution rate is {perf['resolution_rate']}% — "
        f"{perf['resolved']} resolved, {perf['escalated']} escalated, "
        f"{perf['rejected']} rejected, {perf['active']} still active "
        f"of {perf['total_exceptions']} total exceptions."
    )


def _answer_exception(exc, investigation):
    if exc is None:
        return "That exception could not be found."
    parts = [
        f"{exc['exception_id']} is a {exc['type']} exception ({exc['status']}, "
        f"{exc['severity']} severity, risk {exc['risk_score']}).",
        f"Expected {format_inr(exc.get('expected_amount') or 0)}, actual "
        f"{format_inr(exc.get('actual_amount') or 0)}, potential leakage "
        f"{format_inr(exc['potential_leakage'])}.",
    ]
    if investigation:
        parts.append(
            f"AI investigation classified it as {investigation['classification']} "
            f"(confidence {investigation['confidence']}, recommends "
            f"{investigation['recommended_action']}). This is advisory — a human "
            f"finance controller makes the final decision."
        )
    else:
        parts.append("No AI investigation has been run for this exception yet.")
    return " ".join(parts)


def query(message: str):
    """Route a natural-language question through the controlled tool registry."""
    intent, exc_id = detect_intent(message)
    tools_used = []
    data = None

    if intent in ("EXCEPTION_INVESTIGATION", "EXCEPTION_EXPLANATION"):
        exc = _call_tool("get_exception", exc_id)
        tools_used.append("get_exception")
        investigation = None
        if exc is not None:
            investigation = investigation_service.get_latest_investigation(exc_id)
            tools_used.append("get_investigation")
        answer = _answer_exception(exc, investigation)
        data = {"exception": exc, "investigation": investigation}
    elif intent == "RISK_PRIORITIES":
        result = _call_tool("get_risk_priorities", limit=5)
        tools_used.append("get_risk_priorities")
        answer = _answer_risk(result["data"])
        data = result
    elif intent == "FINANCIAL_IMPACT":
        result = _call_tool("get_exception_financial_impact")
        tools_used.append("get_exception_financial_impact")
        answer = _answer_impact(result["data"])
        data = result
    elif intent == "LEAKAGE_TREND":
        result = _call_tool("get_leakage_trend")
        tools_used.append("get_leakage_trend")
        answer = _answer_leakage_trend(result)
        data = result
    elif intent == "RESOLUTION_PERFORMANCE":
        result = _call_tool("get_resolution_performance")
        tools_used.append("get_resolution_performance")
        answer = _answer_resolution(result)
        data = result
    else:  # ANALYTICS_SUMMARY
        result = _call_tool("get_analytics_summary")
        tools_used.append("get_analytics_summary")
        answer = _answer_summary(result)
        data = result

    return {"intent": intent, "answer": answer, "tools_used": tools_used, "data": data}
