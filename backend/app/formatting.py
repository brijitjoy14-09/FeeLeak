"""Shared display formatting for backend-generated text (e.g. AI insights)."""

from decimal import Decimal


def _group_indian(int_str: str) -> str:
    if len(int_str) <= 3:
        return int_str
    last3 = int_str[-3:]
    rest = int_str[:-3]
    # Insert a comma before every group of two digits.
    out = ""
    while len(rest) > 2:
        out = "," + rest[-2:] + out
        rest = rest[:-2]
    return rest + out + "," + last3


def format_inr(value) -> str:
    """Format a number as Indian Rupees: 24850 -> '₹24,850'."""
    if value in (None, ""):
        return "—"
    num = Decimal(str(value))
    sign = "-" if num < 0 else ""
    whole = str(int(abs(num)))
    return f"{sign}₹{_group_indian(whole)}"
