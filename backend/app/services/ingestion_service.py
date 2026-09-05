"""CSV ingestion: validation → normalization → in-memory storage.

Financial-integrity rules enforced here:
  * The WHOLE dataset is validated before anything is stored. On any error we
    raise and never partially store (a failed replacement leaves the existing
    valid dataset intact — see `ingest`).
  * Amounts are parsed into `Decimal` (never float); negatives are rejected.
  * Invalid rows are reported, never silently dropped or zero-filled.
  * Identifiers are trimmed but never otherwise mutated (ORD-001 stays ORD-001).
"""

import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

import pandas as pd

from ..config import (
    ACCEPTED_DATE_FORMATS,
    SOURCE_SCHEMAS,
    SUPPORTED_CURRENCIES,
    SUPPORTED_SOURCES,
)
from ..errors import AppError
from ..stores.data_store import store

# Priority used to pick the primary error code when a dataset has several
# kinds of row errors (higher = reported first).
_ROW_ERROR_PRIORITY = {
    "INVALID_AMOUNT": 4,
    "INVALID_DATE": 3,
    "INVALID_CURRENCY": 2,
    "INVALID_DATA": 1,
}
_MAX_REPORTED_ERRORS = 50


def normalize_column(name: str) -> str:
    """Canonicalize a header: trim, lowercase, spaces/hyphens -> underscore."""
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def _parse_amount(raw: str) -> Decimal:
    """Parse a money string into Decimal. Raises ValueError on bad input."""
    cleaned = raw.strip().replace(",", "")
    try:
        value = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError("not a number") from exc
    if not value.is_finite():
        raise ValueError("not finite")
    return value


def _normalize_date(raw: str) -> str:
    """Validate a date and normalize to YYYY-MM-DD (preserving time if given)."""
    value = raw.strip()
    for fmt in ACCEPTED_DATE_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt)
        except ValueError:
            continue
        if "%H" in fmt:
            # Preserve meaningful timestamp information.
            return parsed.isoformat()
        return parsed.strftime("%Y-%m-%d")
    raise ValueError("invalid date")


def _read_csv(raw_bytes: bytes, source_type: str) -> pd.DataFrame:
    if not raw_bytes or not raw_bytes.strip():
        raise AppError("EMPTY_FILE", "The uploaded CSV file is empty.", 400)
    try:
        df = pd.read_csv(
            io.BytesIO(raw_bytes),
            dtype=str,
            keep_default_na=False,
            skip_blank_lines=True,
        )
    except Exception as exc:  # pragma: no cover - defensive, no stack trace leaked
        raise AppError(
            "INVALID_DATA",
            "The uploaded file could not be parsed as CSV.",
            400,
            {"source_type": source_type},
        ) from exc
    df.columns = [normalize_column(c) for c in df.columns]
    if df.shape[1] == 0 or df.shape[0] == 0:
        raise AppError("EMPTY_FILE", "The uploaded CSV file has no data rows.", 400)
    return df


def validate_and_normalize(source_type: str, raw_bytes: bytes):
    """Validate + normalize a CSV for `source_type`.

    Returns (records, columns). Raises AppError on any validation failure.
    """
    if source_type not in SUPPORTED_SOURCES:
        raise AppError(
            "UNSUPPORTED_SOURCE",
            f"Unsupported source type: '{source_type}'.",
            400,
            {"supported_sources": SUPPORTED_SOURCES},
        )

    schema = SOURCE_SCHEMAS[source_type]
    df = _read_csv(raw_bytes, source_type)

    # --- required columns ---
    missing = [c for c in schema["required"] if c not in df.columns]
    if missing:
        raise AppError(
            "MISSING_COLUMNS",
            "Required columns are missing.",
            422,
            {"source_type": source_type, "missing_columns": missing},
        )

    columns = list(df.columns)
    amount_fields = set(schema["amount_fields"])
    date_fields = set(schema["date_fields"])
    id_fields = set(schema["ref_id_fields"])
    currency_field = schema["currency_field"]

    records = []
    errors = []

    for idx, row in enumerate(df.to_dict(orient="records")):
        row_number = idx + 2  # +1 header, +1 to 1-index
        record = {}
        for col in columns:
            raw_value = row.get(col, "")
            value = raw_value.strip() if isinstance(raw_value, str) else raw_value

            if col in id_fields:
                if value == "":
                    errors.append(
                        {
                            "row": row_number,
                            "field": col,
                            "code": "INVALID_DATA",
                            "message": f"'{col}' is required and cannot be empty.",
                        }
                    )
                record[col] = value  # identifiers preserved verbatim (trimmed)
            elif col in amount_fields:
                try:
                    amount = _parse_amount(value)
                except ValueError:
                    errors.append(
                        {
                            "row": row_number,
                            "field": col,
                            "code": "INVALID_AMOUNT",
                            "message": f"'{col}' must be a number (got '{value}').",
                        }
                    )
                    record[col] = value
                    continue
                if amount < 0:
                    errors.append(
                        {
                            "row": row_number,
                            "field": col,
                            "code": "INVALID_AMOUNT",
                            "message": f"'{col}' must not be negative (got '{value}').",
                        }
                    )
                record[col] = amount
            elif col in date_fields:
                try:
                    record[col] = _normalize_date(value)
                except ValueError:
                    errors.append(
                        {
                            "row": row_number,
                            "field": col,
                            "code": "INVALID_DATE",
                            "message": f"'{col}' is not a valid date (got '{value}').",
                        }
                    )
                    record[col] = value
            elif col == currency_field:
                normalized = value.upper()
                if normalized not in SUPPORTED_CURRENCIES:
                    errors.append(
                        {
                            "row": row_number,
                            "field": col,
                            "code": "INVALID_CURRENCY",
                            "message": (
                                f"Unsupported currency '{value}'. "
                                f"Supported: {', '.join(sorted(SUPPORTED_CURRENCIES))}."
                            ),
                        }
                    )
                record[col] = normalized
            else:
                record[col] = value

        records.append(record)

    if errors:
        primary = max(errors, key=lambda e: _ROW_ERROR_PRIORITY.get(e["code"], 0))
        raise AppError(
            primary["code"],
            "The dataset failed validation.",
            422,
            {
                "source_type": source_type,
                "error_count": len(errors),
                "errors": errors[:_MAX_REPORTED_ERRORS],
            },
        )

    return records, columns


def ingest(source_type: str, raw_bytes: bytes, filename: str):
    """Validate, normalize, and store a dataset (replacing any existing one).

    Storage only happens after full validation succeeds, so a failed upload
    never destroys the previously loaded valid dataset.
    """
    records, columns = validate_and_normalize(source_type, raw_bytes)

    replaced = store.has_dataset(source_type)
    dataset = {
        "source_type": source_type,
        "records": records,
        "columns": columns,
        "record_count": len(records),
        "uploaded_at": datetime.now().astimezone().isoformat(),
        "filename": filename,
        "status": "loaded",
    }
    store.put_dataset(source_type, dataset)
    # A new dataset invalidates any prior reconciliation run.
    store.set_reconciliation(None)

    return dataset, replaced


def serialize_record(record: dict) -> dict:
    """Convert a normalized record to JSON-safe values (Decimal -> string)."""
    out = {}
    for key, value in record.items():
        out[key] = str(value) if isinstance(value, Decimal) else value
    return out
