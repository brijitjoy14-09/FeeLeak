"""Pydantic response models for the ingestion API (explicit API contracts)."""

from typing import List, Optional

from pydantic import BaseModel


class IngestionResponse(BaseModel):
    success: bool = True
    source_type: str
    record_count: int
    columns: List[str]
    status: str
    replaced: bool
    uploaded_at: str
    message: str


class SourceStatus(BaseModel):
    loaded: bool
    records: int


class StatusResponse(BaseModel):
    sources: dict[str, SourceStatus]


class DatasetMetadata(BaseModel):
    source_type: str
    record_count: int
    status: str
    columns: List[str]
    uploaded_at: Optional[str] = None
    filename: Optional[str] = None


class DatasetListResponse(BaseModel):
    datasets: List[DatasetMetadata]


class DatasetRecordsResponse(BaseModel):
    source_type: str
    record_count: int
    returned: int
    limit: Optional[int] = None
    columns: List[str]
    records: List[dict]


class DeleteResponse(BaseModel):
    success: bool = True
    source_type: str
