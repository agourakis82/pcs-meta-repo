"""Pydantic models for the PCS-HELIO MCP API."""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class RAGQuery(BaseModel):
    """Model for RAG (Retrieval-Augmented Generation) query requests."""

    query: str = Field(
        ..., description="The user's question or query", min_length=1, max_length=1000
    )
    max_results: Optional[int] = Field(
        default=5, description="Maximum number of results to retrieve", ge=1, le=20
    )
    similarity_threshold: Optional[float] = Field(
        default=0.7, description="Minimum similarity score for results", ge=0.0, le=1.0
    )
    include_metadata: Optional[bool] = Field(
        default=True, description="Whether to include document metadata in results"
    )


class DocumentSource(BaseModel):
    """Model for document source information."""

    title: str = Field(..., description="Document title")
    source: str = Field(..., description="Source identifier or filename")
    page: Optional[int] = Field(None, description="Page number if applicable")
    chunk_id: Optional[str] = Field(None, description="Chunk identifier")
    similarity_score: Optional[float] = Field(
        None, description="Similarity score", ge=0.0, le=1.0
    )
    metadata: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )


class RAGAnswer(BaseModel):
    """Model for RAG query responses."""

    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    sources: List[DocumentSource] = Field(
        default_factory=list, description="Source documents used for the answer"
    )
    confidence_score: Optional[float] = Field(
        None, description="Confidence score for the answer", ge=0.0, le=1.0
    )
    processing_time_ms: Optional[float] = Field(
        None, description="Processing time in milliseconds", ge=0.0
    )
    model_used: Optional[str] = Field(None, description="AI model used for generation")


class UploadResponse(BaseModel):
    """Model for file upload responses."""

    filename: str = Field(..., description="Uploaded filename")
    file_size: int = Field(..., description="File size in bytes", ge=0)
    file_type: str = Field(..., description="MIME type of the file")
    upload_timestamp: datetime = Field(
        default_factory=datetime.now, description="When the file was uploaded"
    )
    file_id: Optional[str] = Field(
        None, description="Unique identifier for the uploaded file"
    )
    processing_status: str = Field(
        default="uploaded", description="Current processing status"
    )
    error_message: Optional[str] = Field(
        None, description="Error message if upload failed"
    )


class KECItem(BaseModel):
    """Model for Knowledge Exchange and Collaboration items."""

    item_id: str = Field(..., description="Unique identifier")
    title: str = Field(..., description="Item title", min_length=1)
    description: Optional[str] = Field(None, description="Item description")
    item_type: str = Field(
        ..., description="Type of KEC item (paper, dataset, tool, etc.)"
    )
    authors: List[str] = Field(default_factory=list, description="List of authors")
    tags: List[str] = Field(default_factory=list, description="Associated tags")
    url: Optional[str] = Field(None, description="URL to the item")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    publication_date: Optional[datetime] = Field(None, description="Publication date")
    created_at: datetime = Field(
        default_factory=datetime.now, description="When the item was added"
    )
    updated_at: Optional[datetime] = Field(
        None, description="When the item was last updated"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )


class HELIOSummary(BaseModel):
    """
    Model for HELIO (Health, Environment, Labor Information Observatory) summaries.
    """

    summary_id: str = Field(..., description="Unique summary identifier")
    title: str = Field(..., description="Summary title", min_length=1)
    abstract: Optional[str] = Field(None, description="Brief abstract of the summary")
    data_sources: List[str] = Field(
        default_factory=list, description="List of data sources used"
    )
    geographic_scope: Optional[str] = Field(None, description="Geographic area covered")
    temporal_scope: Optional[str] = Field(None, description="Time period covered")
    methodology: Optional[str] = Field(
        None, description="Methodology used for analysis"
    )
    key_findings: List[str] = Field(
        default_factory=list, description="Key findings from the analysis"
    )
    indicators: List[str] = Field(
        default_factory=list, description="Health/environmental indicators analyzed"
    )
    data_quality_score: Optional[float] = Field(
        None, description="Data quality assessment score", ge=0.0, le=1.0
    )
    created_by: Optional[str] = Field(None, description="Creator of the summary")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    version: str = Field(default="1.0", description="Version of the summary")
    status: str = Field(
        default="draft",
        description="Status of the summary (draft, published, archived)",
    )


class HealthResponse(BaseModel):
    """Model for health check responses."""

    ok: bool = Field(..., description="Overall health status")
    uptime_s: float = Field(..., description="Uptime in seconds", ge=0)
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Health check timestamp"
    )
    services: dict[str, Any] = Field(
        default_factory=dict, description="Status of individual services"
    )
    version: Optional[str] = Field(None, description="API version")


class VersionResponse(BaseModel):
    """Model for version information responses."""

    api_version: str = Field(..., description="API version")
    git_sha: Optional[str] = Field(None, description="Git commit SHA")
    build_timestamp: Optional[datetime] = Field(None, description="Build timestamp")
    model_versions: dict[str, str] = Field(
        default_factory=dict, description="AI model versions used"
    )
    repository: dict[str, Any] = Field(
        default_factory=dict, description="Repository information including DOI"
    )


class ErrorResponse(BaseModel):
    """Model for error responses."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(
        None, description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Error timestamp"
    )
    request_id: Optional[str] = Field(
        None, description="Request identifier for tracing"
    )


class PaginationParams(BaseModel):
    """Model for pagination parameters."""

    page: int = Field(default=1, description="Page number", ge=1)
    limit: int = Field(default=20, description="Number of items per page", ge=1, le=100)
    offset: Optional[int] = Field(None, description="Number of items to skip", ge=0)


class PaginatedResponse(BaseModel):
    """Model for paginated responses."""

    items: List[Any] = Field(default_factory=list, description="List of items")
    total: int = Field(..., description="Total number of items", ge=0)
    page: int = Field(..., description="Current page number", ge=1)
    limit: int = Field(..., description="Items per page", ge=1)
    pages: int = Field(..., description="Total number of pages", ge=0)
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
