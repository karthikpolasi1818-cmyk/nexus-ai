from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# NEXUS API SCHEMAS
# ============================================================
#
# Central Pydantic schema definitions for the NEXUS AI API.
#
# Design goals:
#   - Pydantic v2 compatible
#   - Backward compatible with existing routes
#   - Flexible analytics responses
#   - Strict request validation
#   - Safe handling of additional metadata
#
# ============================================================


# ============================================================
# BASE MODEL
# ============================================================


class NexusBaseModel(BaseModel):
    """
    Base Pydantic model used throughout the NEXUS API.

    Extra fields are ignored so clients may send harmless
    metadata without breaking the API contract.
    """

    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
    )


# ============================================================
# HEALTH RESPONSE
# ============================================================


class HealthResponse(NexusBaseModel):
    """
    API health-check response.
    """

    status: str = "healthy"

    service: str = "NEXUS AI"

    version: str = "4.0"

    timestamp: str | None = None

    details: dict[str, Any] = Field(
        default_factory=dict
    )


# ============================================================
# DATASET REQUEST
# ============================================================


class DatasetRequest(NexusBaseModel):
    """
    Common dataset request used by:

        /api/validate
        /api/analyze
        /api/report

    CSV data is transmitted as plain text.
    """

    csv_data: str = Field(
        ...,
        min_length=1,
        description="CSV dataset content as text.",
    )

    target: str | None = Field(
        default=None,
        min_length=1,
        description="Target column for analysis.",
    )

    filename: str | None = Field(
        default="dataset.csv",
        description="Original dataset filename.",
    )


# ============================================================
# VALIDATION REQUEST
# ============================================================


class ValidationRequest(NexusBaseModel):
    """
    Request specifically intended for dataset validation.
    """

    csv_data: str = Field(
        ...,
        min_length=1,
        description="CSV dataset content.",
    )

    target: str = Field(
        ...,
        min_length=1,
        description="Target column for validation.",
    )

    filename: str | None = Field(
        default=None,
        description="Original dataset filename.",
    )


# ============================================================
# VALIDATION RESPONSE
# ============================================================


class ValidationResponse(NexusBaseModel):
    """
    Dataset validation response.
    """

    valid: bool

    status: str

    message: str

    rows: int = 0

    columns: int = 0

    target: str | None = None

    details: dict[str, Any] = Field(
        default_factory=dict
    )


# ============================================================
# ANALYSIS REQUEST
# ============================================================


class AnalysisRequest(NexusBaseModel):
    """
    Request for the complete NEXUS intelligence pipeline.
    """

    csv_data: str = Field(
        ...,
        min_length=1,
        description="CSV dataset content.",
    )

    target: str = Field(
        ...,
        min_length=1,
        description="Target column to analyze.",
    )

    filename: str | None = Field(
        default=None,
        description="Original dataset filename.",
    )

    include_insights: bool = Field(
        default=True,
        description="Generate business insights.",
    )

    include_validation: bool = Field(
        default=True,
        description="Run dataset validation.",
    )


# ============================================================
# ANALYSIS RESPONSE
# ============================================================


class AnalysisResponse(NexusBaseModel):
    """
    Complete NEXUS analysis response.

    The results field intentionally accepts arbitrary nested
    analytics structures because the NEXUS intelligence engine
    contains multiple specialized analytical modules.
    """

    success: bool

    status: str

    message: str

    target: str | None = None

    rows: int = 0

    columns: int = 0

    filename: str | None = None

    timestamp: str | None = None

    results: dict[str, Any] = Field(
        default_factory=dict
    )


# ============================================================
# REPORT REQUEST
# ============================================================


class ReportRequest(NexusBaseModel):
    """
    Request to generate a PDF report.
    """

    csv_data: str = Field(
        ...,
        min_length=1,
        description="CSV dataset content.",
    )

    target: str = Field(
        ...,
        min_length=1,
        description="Target column.",
    )

    filename: str | None = Field(
        default=None,
        description="Original dataset filename.",
    )


# ============================================================
# REPORT RESPONSE
# ============================================================


class ReportResponse(NexusBaseModel):
    """
    Metadata returned after report generation.

    The actual PDF is returned as application/pdf.
    """

    success: bool

    message: str

    filename: str

    content_type: str = (
        "application/pdf"
    )

    size_bytes: int = 0


# ============================================================
# ERROR RESPONSE
# ============================================================


class ErrorResponse(NexusBaseModel):
    """
    Standard NEXUS API error response.
    """

    success: bool = False

    error: str

    code: str = "NEXUS_API_ERROR"

    message: str | None = None

    details: dict[str, Any] = Field(
        default_factory=dict
    )


# ============================================================
# GENERIC API RESPONSE
# ============================================================


class APIResponse(NexusBaseModel):
    """
    Generic API response wrapper.
    """

    success: bool

    status: str = "success"

    message: str = ""

    data: dict[str, Any] = Field(
        default_factory=dict
    )


# ============================================================
# ANALYSIS METADATA
# ============================================================


class AnalysisMetadata(NexusBaseModel):
    """
    Metadata describing an analysis execution.
    """

    filename: str | None = None

    target: str | None = None

    rows: int = 0

    columns: int = 0

    timestamp: str | None = None

    duration_seconds: float | None = None


# ============================================================
# API INFORMATION
# ============================================================


class APIInfoResponse(NexusBaseModel):
    """
    Root API information response.
    """

    name: str = "NEXUS AI"

    description: str = (
        "Autonomous Enterprise Intelligence API"
    )

    version: str = "4.0"

    status: str = "online"

    endpoints: list[str] = Field(
        default_factory=lambda: [
            "/",
            "/health",
            "/validate",
            "/analyze",
            "/report",
        ]
    )