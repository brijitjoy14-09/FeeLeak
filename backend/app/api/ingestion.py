"""Ingestion API routes.

Thin HTTP layer: parse the request, delegate to the ingestion service, and
shape the response. No validation/normalization logic lives here.
"""

from typing import Optional

from fastapi import APIRouter, File, Form, Query, UploadFile

from ..config import SUPPORTED_SOURCES
from ..errors import AppError
from ..schemas.ingestion import (
    DatasetListResponse,
    DatasetMetadata,
    DatasetRecordsResponse,
    DeleteResponse,
    IngestionResponse,
    SourceStatus,
    StatusResponse,
)
from ..services import ingestion_service
from ..stores.data_store import store

router = APIRouter(prefix="/api/v1/ingestion", tags=["ingestion"])

_ALLOWED_EXTENSIONS = (".csv",)
_ALLOWED_CONTENT_TYPES = {"text/csv", "application/csv", "application/vnd.ms-excel", ""}


def _validate_source_type(source_type: str) -> None:
    if source_type not in SUPPORTED_SOURCES:
        raise AppError(
            "UNSUPPORTED_SOURCE",
            f"Unsupported source type: '{source_type}'.",
            400,
            {"supported_sources": SUPPORTED_SOURCES},
        )


def _validate_is_csv(upload: UploadFile) -> None:
    name = (upload.filename or "").lower()
    is_csv_ext = name.endswith(_ALLOWED_EXTENSIONS)
    content_type_ok = (upload.content_type or "") in _ALLOWED_CONTENT_TYPES
    # Filename is used only for this extension check + metadata, never for
    # storage keys or filesystem paths.
    if not is_csv_ext and not content_type_ok:
        raise AppError(
            "INVALID_FILE_TYPE",
            "Only CSV files are supported.",
            400,
            {"filename": upload.filename},
        )


@router.post("/upload", response_model=IngestionResponse)
async def upload_dataset(
    source_type: str = Form(...),
    file: UploadFile = File(...),
):
    _validate_source_type(source_type)
    _validate_is_csv(file)

    raw_bytes = await file.read()
    dataset, replaced = ingestion_service.ingest(source_type, raw_bytes, file.filename)

    message = (
        f"{source_type} replaced: {dataset['record_count']} records loaded."
        if replaced
        else f"{source_type} uploaded successfully: {dataset['record_count']} records loaded."
    )
    return IngestionResponse(
        source_type=source_type,
        record_count=dataset["record_count"],
        columns=dataset["columns"],
        status=dataset["status"],
        replaced=replaced,
        uploaded_at=dataset["uploaded_at"],
        message=message,
    )


@router.get("/status", response_model=StatusResponse)
async def ingestion_status():
    sources = {}
    for source in SUPPORTED_SOURCES:
        dataset = store.get_dataset(source)
        sources[source] = SourceStatus(
            loaded=dataset is not None,
            records=dataset["record_count"] if dataset else 0,
        )
    return StatusResponse(sources=sources)


@router.get("/datasets", response_model=DatasetListResponse)
async def list_datasets():
    datasets = []
    for source in SUPPORTED_SOURCES:
        dataset = store.get_dataset(source)
        if not dataset:
            continue
        datasets.append(
            DatasetMetadata(
                source_type=dataset["source_type"],
                record_count=dataset["record_count"],
                status=dataset["status"],
                columns=dataset["columns"],
                uploaded_at=dataset.get("uploaded_at"),
                filename=dataset.get("filename"),
            )
        )
    return DatasetListResponse(datasets=datasets)


@router.get("/datasets/{source_type}", response_model=DatasetRecordsResponse)
async def get_dataset(
    source_type: str,
    limit: Optional[int] = Query(default=100, ge=1, le=5000),
):
    _validate_source_type(source_type)
    dataset = store.get_dataset(source_type)
    if not dataset:
        raise AppError(
            "DATASET_NOT_FOUND",
            f"No dataset loaded for source '{source_type}'.",
            404,
            {"source_type": source_type},
        )

    records = dataset["records"]
    limited = records[:limit] if limit is not None else records
    serialized = [ingestion_service.serialize_record(r) for r in limited]
    return DatasetRecordsResponse(
        source_type=source_type,
        record_count=dataset["record_count"],
        returned=len(serialized),
        limit=limit,
        columns=dataset["columns"],
        records=serialized,
    )


@router.delete("/datasets/{source_type}", response_model=DeleteResponse)
async def delete_dataset(source_type: str):
    _validate_source_type(source_type)
    removed = store.delete_dataset(source_type)
    if removed is None:
        raise AppError(
            "DATASET_NOT_FOUND",
            f"No dataset loaded for source '{source_type}'.",
            404,
            {"source_type": source_type},
        )
    # Deleting a dataset invalidates any prior reconciliation run.
    store.set_reconciliation(None)
    return DeleteResponse(source_type=source_type)
