# FeeLeak — Sample Test Data

Ready-to-upload demo CSVs that exercise every reconciliation, exception, risk,
and AI-investigation scenario in FeeLeak. All values are **synthetic**, in
**INR**, and use `YYYY-MM-DD` dates.

## Files

| File | Rows | Source type to select on upload |
| --- | --- | --- |
| `orders.csv` | 16 | Orders |
| `payments.csv` | 18 (incl. 1 duplicate) | Payments |
| `refunds.csv` | 4 | Refunds |
| `fees.csv` | 19 | Fees |
| `settlements.csv` | 17 | Settlements |

`invalid_examples/` holds intentionally broken files for testing validation
(see the bottom of this file).

## How to use

1. Start the backend and frontend, open **http://localhost:5173**.
2. Go to **Reconciliation**. For each of the five sources, choose the matching
   **Source** in the dropdown and upload the file of the same name above.
3. Click **Run Reconciliation**.
4. Go to **Exceptions** and click **Generate Exceptions**.
5. Explore **Analytics** and the **Copilot**; open an exception to investigate,
   then Resolve / Escalate / Reject it.

## Expected results (ground truth)

**Reconciliation summary**

| Metric | Value |
| --- | ---: |
| Total payment rows | 18 |
| Matched | 10 |
| Mismatched | 3 |
| Missing settlement | 2 |
| Order not found | 1 |
| Duplicate payment rows | 2 |
| Orphan settlements / refunds / fees | 1 / 1 / 1 |
| Total difference (potential leakage) | ₹39,671 |
| Match rate | 55.6% |

> The duplicate payment `PAY013` appears twice on purpose, so there are 18
> payment rows for 17 unique payments — this is what raises the
> `DUPLICATE_PAYMENT` exception.

**Exceptions generated: 10 total**

| Exception | Payment | Type | Severity | Potential leakage |
| --- | --- | --- | --- | ---: |
| Critical missing settlement | PAY005 | Missing Settlement | CRITICAL | ₹29,410 |
| Missing settlement | PAY004 | Missing Settlement | MEDIUM | ₹4,823 |
| Large amount mismatch | PAY011 | Amount Mismatch | MEDIUM | ₹4,528 |
| Refund-related mismatch | PAY003 | Amount Mismatch | MEDIUM | ₹646 |
| Fee-related mismatch | PAY002 | Amount Mismatch | LOW | ₹264 |
| Order not found | PAY012 | Order Not Found | HIGH | ₹0 |
| Duplicate payment | PAY013 | Duplicate Payment | MEDIUM | ₹0 |
| Orphan settlement | SET900 | Orphan Settlement | MEDIUM | ₹0 |
| Orphan refund | REF900 | Orphan Refund | MEDIUM | ₹0 |
| Orphan fee | FEE900 | Orphan Fee | LOW | ₹0 |

Severity distribution: **LOW 2 · MEDIUM 6 · HIGH 1 · CRITICAL 1**.
Data-integrity issues (order-not-found, duplicate, orphans) carry **₹0 leakage**
by design — they are integrity problems, not unexplained money.

### Worked example (PAY003 — refund-related mismatch)

```
Payment            ₹15,000
− Refunds (REF001)  ₹2,000
− Fees (FEE003)       ₹300
− Taxes                ₹54
────────────────────────────
Expected settlement ₹12,646
Actual settlement   ₹12,000   (SET003)
Difference             ₹646   → Amount Mismatch, potential leakage ₹646
```

### Matched examples worth opening

- **PAY006** — multiple refunds (₹300 + ₹200), multiple fees, and a **split
  settlement** (₹2,600 + ₹2,605) that still reconciles to ₹5,205.
- **PAY001, PAY008, PAY015** — clean single-settlement matches.

## Testing validation errors (`invalid_examples/`)

Upload these as the **Payments** source to see FeeLeak's validation messages
(the app never stores an invalid dataset):

| File | Expected error |
| --- | --- |
| `payments_missing_column.csv` | `MISSING_COLUMNS` (no `payment_id`) |
| `payments_bad_amount.csv` | `INVALID_AMOUNT` (amount is `abc`) |
| `payments_negative_amount.csv` | `INVALID_AMOUNT` (negative amount) |
| `payments_bad_currency.csv` | `INVALID_CURRENCY` (USD; INR only) |
| `payments_empty.csv` | `EMPTY_FILE` |
