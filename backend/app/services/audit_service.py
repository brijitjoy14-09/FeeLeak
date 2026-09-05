"""Audit trail (Prompt 8): a single append-only log of who/what/when/why.

Every material event (exception created, AI investigation, review started,
resolved, escalated, rejected) is recorded here. There is exactly one audit
system — services call `record` rather than writing events themselves.
"""

from datetime import datetime

from ..stores.data_store import store


def record(event_type, exception_id, actor, detail=None, reason=None):
    """Append one audit event and return it."""
    return store.add_audit(
        {
            "event_type": event_type,
            "exception_id": exception_id,
            "actor": actor,
            "timestamp": datetime.now().astimezone().isoformat(),
            "detail": detail,
            "reason": reason,
        }
    )


def for_exception(exception_id):
    """Audit events for one exception, oldest first."""
    return sorted(store.get_audit(exception_id), key=lambda e: e["seq"])


def all_events():
    return sorted(store.get_audit(), key=lambda e: e["seq"])
