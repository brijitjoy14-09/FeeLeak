"""In-memory dataset + reconciliation store for the MVP.

NOTE: This is deliberately in-memory only. No database (Postgres/SQLite/etc.)
is introduced in this phase. The store is a single process-wide singleton so
ingestion and reconciliation share the same data. Persistent storage can be
introduced later behind this same interface without touching callers.
"""

from threading import RLock


class DataStore:
    def __init__(self):
        self._lock = RLock()
        # source_type -> {records, columns, record_count, uploaded_at,
        #                 filename, status}
        self.datasets = {}
        # Latest reconciliation run result (or None).
        self.reconciliation = None
        # exception_id -> exception dict (Prompt 5).
        self.exceptions = {}
        # exception_id -> list of investigation dicts, newest last (Prompt 6).
        self.investigations = {}
        # Append-only audit events (Prompt 8), plus a monotonic counter.
        self.audit_events = []
        self._audit_seq = 0

    # ---- Datasets ---------------------------------------------------------
    def put_dataset(self, source_type, dataset):
        with self._lock:
            self.datasets[source_type] = dataset

    def get_dataset(self, source_type):
        with self._lock:
            return self.datasets.get(source_type)

    def has_dataset(self, source_type):
        with self._lock:
            return source_type in self.datasets

    def delete_dataset(self, source_type):
        with self._lock:
            return self.datasets.pop(source_type, None)

    def records(self, source_type):
        """Return the normalized records for a source, or [] if not loaded."""
        with self._lock:
            dataset = self.datasets.get(source_type)
            return dataset["records"] if dataset else []

    # ---- Reconciliation ---------------------------------------------------
    def set_reconciliation(self, result):
        with self._lock:
            self.reconciliation = result

    def get_reconciliation(self):
        with self._lock:
            return self.reconciliation

    # ---- Exceptions (Prompt 5) -------------------------------------------
    def set_exceptions(self, exceptions):
        """Replace the exception set with {exception_id: exception}."""
        with self._lock:
            self.exceptions = exceptions

    def get_exceptions(self):
        with self._lock:
            return self.exceptions

    def get_exception(self, exception_id):
        with self._lock:
            return self.exceptions.get(exception_id)

    def put_exception(self, exception):
        with self._lock:
            self.exceptions[exception["exception_id"]] = exception

    # ---- Investigations (Prompt 6) ---------------------------------------
    def add_investigation(self, exception_id, investigation):
        with self._lock:
            self.investigations.setdefault(exception_id, []).append(investigation)

    def get_investigations(self, exception_id):
        with self._lock:
            return list(self.investigations.get(exception_id, []))

    def get_latest_investigation(self, exception_id):
        with self._lock:
            history = self.investigations.get(exception_id)
            return history[-1] if history else None

    # ---- Audit trail (Prompt 8) ------------------------------------------
    def add_audit(self, event):
        """Append an audit event; assigns a monotonic audit_id + sequence."""
        with self._lock:
            self._audit_seq += 1
            event = {**event, "audit_id": f"AUD-{self._audit_seq:05d}",
                     "seq": self._audit_seq}
            self.audit_events.append(event)
            return event

    def get_audit(self, exception_id=None):
        with self._lock:
            if exception_id is None:
                return list(self.audit_events)
            return [e for e in self.audit_events if e.get("exception_id") == exception_id]

    # ---- Testing / lifecycle ---------------------------------------------
    def reset(self):
        with self._lock:
            self.datasets = {}
            self.reconciliation = None
            self.exceptions = {}
            self.investigations = {}
            self.audit_events = []
            self._audit_seq = 0


# Process-wide singleton.
store = DataStore()
