"""Ingestion API tests (kept focused on the core validation guarantees)."""

from tests.conftest import upload

ORDERS_100 = "order_id,order_date,customer_id,order_amount,currency,status\n" + "".join(
    f"ORD{i:03d},2026-08-01,CUST{i:03d},1000,INR,completed\n" for i in range(1, 101)
)
ORDERS_50 = "order_id,order_date,customer_id,order_amount,currency,status\n" + "".join(
    f"ORD{i:03d},2026-08-01,CUST{i:03d},1000,INR,completed\n" for i in range(1, 51)
)


def test_valid_orders_upload(client, fixture_bytes):
    resp = upload(client, "orders", "orders.csv", fixture_bytes("orders.csv"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["source_type"] == "orders"
    assert body["record_count"] == 7


def test_valid_payments_upload_is_stored(client, fixture_bytes):
    upload(client, "payments", "payments.csv", fixture_bytes("payments.csv"))
    status = client.get("/api/v1/ingestion/status").json()
    assert status["sources"]["payments"]["loaded"] is True
    assert status["sources"]["payments"]["records"] == 8


def test_missing_required_column_not_stored(client):
    csv = "order_id,payment_date,payment_amount,currency,payment_status\nPAY1,2026-08-01,10,INR,captured\n"
    resp = upload(client, "payments", "payments.csv", csv)
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "MISSING_COLUMNS"
    assert "payment_id" in body["error"]["details"]["missing_columns"]
    # Nothing stored.
    assert client.get("/api/v1/ingestion/status").json()["sources"]["payments"]["loaded"] is False


def test_invalid_amount(client):
    csv = "payment_id,order_id,payment_date,payment_amount,currency,payment_status\nPAY1,ORD1,2026-08-01,abc,INR,captured\n"
    resp = upload(client, "payments", "payments.csv", csv)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_AMOUNT"


def test_negative_amount(client):
    csv = "payment_id,order_id,payment_date,payment_amount,currency,payment_status\nPAY1,ORD1,2026-08-01,-50,INR,captured\n"
    resp = upload(client, "payments", "payments.csv", csv)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_AMOUNT"


def test_invalid_date(client):
    csv = "payment_id,order_id,payment_date,payment_amount,currency,payment_status\nPAY1,ORD1,not-a-date,100,INR,captured\n"
    resp = upload(client, "payments", "payments.csv", csv)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_DATE"


def test_unsupported_currency(client):
    csv = "payment_id,order_id,payment_date,payment_amount,currency,payment_status\nPAY1,ORD1,2026-08-01,100,USD,captured\n"
    resp = upload(client, "payments", "payments.csv", csv)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_CURRENCY"


def test_empty_csv(client):
    resp = upload(client, "orders", "orders.csv", "")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "EMPTY_FILE"


def test_unsupported_source(client, fixture_bytes):
    resp = upload(client, "invoices", "x.csv", fixture_bytes("orders.csv"))
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "UNSUPPORTED_SOURCE"


def test_non_csv_rejected(client):
    resp = client.post(
        "/api/v1/ingestion/upload",
        data={"source_type": "orders"},
        files={"file": ("orders.json", "{}", "application/json")},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_FILE_TYPE"


def test_status_and_metadata(client, fixture_bytes):
    upload(client, "orders", "orders.csv", fixture_bytes("orders.csv"))
    upload(client, "payments", "payments.csv", fixture_bytes("payments.csv"))

    datasets = client.get("/api/v1/ingestion/datasets").json()["datasets"]
    sources = {d["source_type"]: d for d in datasets}
    assert set(sources) == {"orders", "payments"}
    assert "order_id" in sources["orders"]["columns"]
    # Metadata endpoint must not embed full record rows.
    assert "records" not in sources["orders"]


def test_dataset_retrieval_returns_records(client, fixture_bytes):
    upload(client, "orders", "orders.csv", fixture_bytes("orders.csv"))
    body = client.get("/api/v1/ingestion/datasets/orders?limit=3").json()
    assert body["returned"] == 3
    assert body["record_count"] == 7
    assert body["records"][0]["order_id"] == "ORD001"


def test_delete_dataset(client, fixture_bytes):
    upload(client, "orders", "orders.csv", fixture_bytes("orders.csv"))
    deleted = client.delete("/api/v1/ingestion/datasets/orders")
    assert deleted.status_code == 200
    assert deleted.json()["success"] is True
    missing = client.get("/api/v1/ingestion/datasets/orders")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "DATASET_NOT_FOUND"


def test_replacement_replaces_not_appends(client):
    upload(client, "orders", "orders.csv", ORDERS_100)
    assert client.get("/api/v1/ingestion/status").json()["sources"]["orders"]["records"] == 100
    upload(client, "orders", "orders.csv", ORDERS_50)
    assert client.get("/api/v1/ingestion/status").json()["sources"]["orders"]["records"] == 50


def test_failed_replacement_preserves_existing(client):
    upload(client, "orders", "orders.csv", ORDERS_100)
    bad = "order_id,order_date,customer_id,order_amount,currency,status\nORDX,2026-08-01,C,abc,INR,completed\n"
    resp = upload(client, "orders", "orders.csv", bad)
    assert resp.status_code == 422
    # Original 100-record dataset must survive.
    assert client.get("/api/v1/ingestion/status").json()["sources"]["orders"]["records"] == 100
