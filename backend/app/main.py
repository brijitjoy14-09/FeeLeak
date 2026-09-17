"""FeeLeak API — application setup.

This module is intentionally limited to FastAPI application setup:
metadata, CORS configuration, and the foundational root/health endpoints.

Business logic (reconciliation, leakage detection, AI investigation, etc.)
is deliberately NOT implemented here and will be introduced in later prompts
as dedicated routers/services. Keep this file focused on wiring only.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import (
    analytics,
    copilot,
    exceptions,
    ingestion,
    investigations,
    reconciliation,
)
from .errors import AppError, app_error_handler

# Explicit development origins for the React (Vite) frontend.
# Kept as a list so production origins can be appended later without
# rewriting the application. Unrestricted "*" is intentionally avoided.
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://fee-leak-55ol.vercel.app",
]

app = FastAPI(
    title="FeeLeak API",
    description="AI-powered financial reconciliation backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Domain errors are rendered as a consistent JSON envelope (no stack traces).
app.add_exception_handler(AppError, app_error_handler)

# Feature routers (ingestion = P3, reconciliation = P4, exceptions = P5,
# investigations = P6).
app.include_router(ingestion.router)
app.include_router(reconciliation.router)
app.include_router(exceptions.router)
app.include_router(investigations.router)
app.include_router(analytics.router)
app.include_router(copilot.router)


@app.get("/")
def read_root():
    """Root endpoint used as a basic liveness signal."""
    return {"message": "FeeLeak API is running"}


@app.get("/health")
def health_check():
    """Health endpoint consumed by the frontend to show connection status."""
    return {"status": "healthy"}
