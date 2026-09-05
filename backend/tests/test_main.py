"""Tests for the FeeLeak foundation API."""

import importlib

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """GET / returns 200 and the running message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "FeeLeak API is running"}


def test_health_endpoint():
    """GET /health returns 200 and a healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_app_import():
    """app.main imports successfully and exposes a FastAPI application."""
    module = importlib.import_module("app.main")
    assert hasattr(module, "app")
    assert isinstance(module.app, FastAPI)
