"""Central configuration for FeeLeak backend business logic.

Keeping these values in one place means schemas, validation rules, the
reconciliation tolerance, and API prefixes can be changed without hunting
through the codebase.
"""

from decimal import Decimal

# All ingestion/reconciliation routes live under this prefix.
API_PREFIX = "/api/v1"

# ---- Currency (MVP: INR only; no FX conversion yet) -----------------------
SUPPORTED_CURRENCIES = {"INR"}
DEFAULT_CURRENCY = "INR"

# ---- Reconciliation --------------------------------------------------------
# Configurable monetary tolerance. abs(expected - actual) <= tolerance => MATCHED.
# Defined once here so it is never hardcoded across the engine.
RECONCILIATION_TOLERANCE = Decimal("0.01")

# Display precision for money values returned by the API (2 dp).
MONEY_QUANTIZE = Decimal("0.01")

# ---- Sources & schemas -----------------------------------------------------
# The five supported source types, referenced consistently everywhere.
SUPPORTED_SOURCES = ["orders", "payments", "refunds", "fees", "settlements"]

# Per-source schema metadata used by ingestion validation/normalization.
#   required        : columns that must be present (canonical internal names)
#   id_field        : primary identifier for the source
#   ref_id_fields   : identifier columns that must be non-empty (incl. id_field)
#   amount_fields   : numeric money fields (validated: numeric, non-negative)
#   date_fields     : date fields (validated + normalized to YYYY-MM-DD)
#   currency_field  : currency column (validated against SUPPORTED_CURRENCIES)
SOURCE_SCHEMAS = {
    "orders": {
        "required": [
            "order_id",
            "order_date",
            "customer_id",
            "order_amount",
            "currency",
            "status",
        ],
        "id_field": "order_id",
        "ref_id_fields": ["order_id"],
        "amount_fields": ["order_amount"],
        "date_fields": ["order_date"],
        "currency_field": "currency",
    },
    "payments": {
        "required": [
            "payment_id",
            "order_id",
            "payment_date",
            "payment_amount",
            "currency",
            "payment_status",
        ],
        "id_field": "payment_id",
        "ref_id_fields": ["payment_id", "order_id"],
        "amount_fields": ["payment_amount"],
        "date_fields": ["payment_date"],
        "currency_field": "currency",
    },
    "refunds": {
        "required": [
            "refund_id",
            "payment_id",
            "refund_date",
            "refund_amount",
            "currency",
            "refund_status",
        ],
        "id_field": "refund_id",
        "ref_id_fields": ["refund_id", "payment_id"],
        "amount_fields": ["refund_amount"],
        "date_fields": ["refund_date"],
        "currency_field": "currency",
    },
    "fees": {
        "required": [
            "fee_id",
            "payment_id",
            "fee_date",
            "fee_amount",
            "tax_amount",
            "currency",
            "fee_type",
        ],
        "id_field": "fee_id",
        "ref_id_fields": ["fee_id", "payment_id"],
        "amount_fields": ["fee_amount", "tax_amount"],
        "date_fields": ["fee_date"],
        "currency_field": "currency",
    },
    "settlements": {
        "required": [
            "settlement_id",
            "payment_id",
            "settlement_date",
            "settlement_amount",
            "currency",
            "settlement_status",
        ],
        "id_field": "settlement_id",
        "ref_id_fields": ["settlement_id", "payment_id"],
        "amount_fields": ["settlement_amount"],
        "date_fields": ["settlement_date"],
        "currency_field": "currency",
    },
}

# Accepted input date formats; all normalized to YYYY-MM-DD on ingestion.
ACCEPTED_DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
]


# ===========================================================================
# Exception management (Prompt 5) — all thresholds/weights centralized here.
# ===========================================================================
import os

# Demo identity used when no auth system exists.
DEMO_REVIEWER = "finance-controller"

# Exception lifecycle statuses and the allowed transitions between them.
# REJECTED (Prompt 8) is a terminal decision: the exception is a false positive
# or accepted-as-is; a reason is required, like escalation/resolution.
EXCEPTION_STATUSES = ["OPEN", "IN_REVIEW", "RESOLVED", "ESCALATED", "REJECTED"]
EXCEPTION_TRANSITIONS = {
    "OPEN": {"IN_REVIEW", "ESCALATED", "REJECTED"},
    "IN_REVIEW": {"RESOLVED", "ESCALATED", "REJECTED"},
    "ESCALATED": {"IN_REVIEW", "RESOLVED", "REJECTED"},
    "RESOLVED": set(),  # terminal
    "REJECTED": set(),  # terminal
}
# Statuses that count as "active" (unresolved) for KPIs/leakage.
ACTIVE_EXCEPTION_STATUSES = {"OPEN", "IN_REVIEW", "ESCALATED"}
# Statuses that require a free-text reason when transitioning INTO them.
REASON_REQUIRED_STATUSES = {"RESOLVED", "ESCALATED", "REJECTED"}

# Exception types (one primary exception per reconciliation problem).
EXCEPTION_TYPES = [
    "AMOUNT_MISMATCH",
    "MISSING_SETTLEMENT",
    "ORDER_NOT_FOUND",
    "ORPHAN_SETTLEMENT",
    "ORPHAN_REFUND",
    "ORPHAN_FEE",
    "DUPLICATE_PAYMENT",
]

# Map a reconciliation payment status -> exception type (centralized).
RECON_STATUS_TO_EXCEPTION_TYPE = {
    "MISMATCH": "AMOUNT_MISMATCH",
    "MISSING_SETTLEMENT": "MISSING_SETTLEMENT",
    "ORDER_NOT_FOUND": "ORDER_NOT_FOUND",
    "DUPLICATE_PAYMENT": "DUPLICATE_PAYMENT",
}
# Map an orphan record kind (singular) -> exception type.
ORPHAN_KIND_TO_EXCEPTION_TYPE = {
    "settlement": "ORPHAN_SETTLEMENT",
    "refund": "ORPHAN_REFUND",
    "fee": "ORPHAN_FEE",
}

# Severity thresholds (evaluated on potential_leakage, or affected_amount when
# leakage is zero). Ordered low -> high; first match by upper bound wins.
SEVERITY_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
SEVERITY_THRESHOLDS = [
    ("LOW", Decimal("500")),        # amount < 500
    ("MEDIUM", Decimal("5000")),    # 500 <= amount < 5000
    ("HIGH", Decimal("25000")),     # 5000 <= amount < 25000
    # else CRITICAL (amount >= 25000)
]
SEVERITY_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

# Priority: deterministic composite of severity, financial impact, and a
# per-type operational weight (higher weight = surfaced earlier).
EXCEPTION_TYPE_WEIGHTS = {
    "MISSING_SETTLEMENT": 70,
    "AMOUNT_MISMATCH": 60,
    "DUPLICATE_PAYMENT": 50,
    "ORPHAN_SETTLEMENT": 40,
    "ORDER_NOT_FOUND": 30,
    "ORPHAN_REFUND": 20,
    "ORPHAN_FEE": 10,
}


# ===========================================================================
# AI investigation (Prompt 6) — advisory layer only.
# ===========================================================================
# Credentials/model come from the environment; never hardcode or expose them.
AI_PROVIDER = os.getenv("AI_PROVIDER", "mock")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "mock-model")
AI_TIMEOUT_SECONDS = float(os.getenv("AI_TIMEOUT_SECONDS", "20"))

# Confidence -> recommended action bands (backend-enforced safety).
CONFIDENCE_AUTO_RESOLVE = 90  # >= 90 : AUTO_RESOLVE eligible (advisory only)
CONFIDENCE_REVIEW = 70        # 70-89 : REVIEW ; < 70 : ESCALATE

# Controlled AI vocabularies.
AI_CLASSIFICATIONS = [
    "EXPECTED_FEE",
    "REFUND_RELATED",
    "DUPLICATE_TRANSACTION",
    "MISSING_SETTLEMENT",
    "ORDER_MAPPING_ERROR",
    "DATA_INTEGRITY_ISSUE",
    "UNIDENTIFIED_ADJUSTMENT",
    "INSUFFICIENT_EVIDENCE",
    "OTHER",
]
AI_ACTIONS = ["AUTO_RESOLVE", "REVIEW", "ESCALATE"]


# ===========================================================================
# Risk prioritization (Prompt 9) — deterministic, explainable, 0-100.
# ===========================================================================
# risk = 0.50*amount + 0.25*severity + 0.15*age + 0.10*status  (each 0-100)
RISK_WEIGHTS = {
    "amount": Decimal("0.50"),
    "severity": Decimal("0.25"),
    "age": Decimal("0.15"),
    "status": Decimal("0.10"),
}
# Amount at/above this cap scores 100 on the amount component.
RISK_AMOUNT_CAP = Decimal("25000")
# Age at/above this many days scores 100 on the age component.
RISK_AGE_CAP_DAYS = 30
RISK_SEVERITY_SCORE = {"LOW": 25, "MEDIUM": 50, "HIGH": 75, "CRITICAL": 100}
RISK_STATUS_SCORE = {
    "OPEN": 60,
    "IN_REVIEW": 70,
    "ESCALATED": 100,
    "RESOLVED": 0,
    "REJECTED": 0,
}
# Risk score -> level. Ordered by upper bound (exclusive); else CRITICAL.
RISK_LEVEL_THRESHOLDS = [("LOW", 25), ("MEDIUM", 50), ("HIGH", 75)]  # else CRITICAL


# ===========================================================================
# Finance Controller Copilot (Prompt 7) — controlled intents + read-only tools.
# ===========================================================================
COPILOT_INTENTS = [
    "EXCEPTION_INVESTIGATION",
    "EXCEPTION_EXPLANATION",
    "ANALYTICS_SUMMARY",
    "LEAKAGE_TREND",
    "FINANCIAL_IMPACT",
    "RISK_PRIORITIES",
    "RESOLUTION_PERFORMANCE",
]

# Analytics risk-priorities default/)max page size.
RISK_PRIORITIES_DEFAULT_LIMIT = 10
RISK_PRIORITIES_MAX_LIMIT = 100
