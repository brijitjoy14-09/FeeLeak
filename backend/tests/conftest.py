"""Shared pytest fixtures for FeeLeak backend tests."""

import os

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.stores.data_store import store

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture(autouse=True)
def reset_store():
    """Ensure every test starts with an empty in-memory store."""
    store.reset()
    yield
    store.reset()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def fixture_bytes():
    def _load(name):
        with open(os.path.join(FIXTURES_DIR, name), "rb") as handle:
            return handle.read()

    return _load


def upload(client, source_type, filename, content):
    """Helper: POST a CSV to the ingestion upload endpoint."""
    return client.post(
        "/api/v1/ingestion/upload",
        data={"source_type": source_type},
        files={"file": (filename, content, "text/csv")},
    )
