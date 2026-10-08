# ============================================================
# NEXUS AI
# API ROUTES
# Autonomous Enterprise Intelligence API
# ============================================================

from __future__ import annotations

import io
import json
import time
from datetime import datetime
from typing import Any

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.api.schemas import (
    DatasetRequest,
)

from app.agents.advanced_orchestrator import (
    AdvancedNexusOrchestrator,
)

from app.services.report_generator import (
    generate_report,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api",
    tags=["NEXUS AI"],
)


# ============================================================
# CONSTANTS
# ============================================================

API_VERSION = "4.0"

ENGINE_NAME = (
    "NEXUS AI Autonomous Enterprise Intelligence"
)


# ============================================================
# SAFE JSON SERIALIZER
# ============================================================

def json_safe(value: Any) -> Any:
    """
    Convert pandas / numpy / Python objects into
    JSON-compatible structures.
    """

    if isinstance(value, pd.DataFrame):

        return [
            json_safe(row)
            for row in value.to_dict(
                orient="records"
            )
        ]

    if isinstance(value, pd.Series):

        return {
            str(key): json_safe(item)
            for key, item in value.to_dict().items()
        }

    if isinstance(value, dict):

        return {
            str(key): json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):

        return [
            json_safe(item)
            for item in value
        ]

    # numpy scalar handling
    try:

        if hasattr(value, "item"):

            return value.item()

    except Exception:

        pass

    # timestamps
    if hasattr(value, "isoformat"):

        try:

            return value.isoformat()

        except Exception:

            pass

    return value


# ============================================================
# CSV LOADER
# ============================================================

def load_csv(
    csv_data: str,
) -> pd.DataFrame:
    """
    Convert CSV text into a pandas DataFrame.
    """

    if not isinstance(
        csv_data,
        str,
    ):

        raise ValueError(
            "csv_data must be a string."
        )

    if not csv_data.strip():

        raise ValueError(
            "csv_data cannot be empty."
        )

    try:

        dataframe = pd.read_csv(
            io.StringIO(csv_data)
        )

    except Exception as error:

        raise ValueError(
            f"Unable to parse CSV data: {error}"
        ) from error

    if dataframe.empty:

        raise ValueError(
            "The supplied CSV contains no rows."
        )

    # Normalize column names
    dataframe.columns = [
        str(column).strip()
        for column in dataframe.columns
    ]

    return dataframe


# ============================================================
# BASIC DATA VALIDATION
# ============================================================

def validate_dataframe(
    dataframe: pd.DataFrame,
    target: str | None = None,
) -> dict[str, Any]:
    """
    Perform API-level dataset validation.
    """

    if not isinstance(
        dataframe,
        pd.DataFrame,
    ):

        raise ValueError(
            "Dataset must be a pandas DataFrame."
        )

    if dataframe.empty:

        raise ValueError(
            "Dataset is empty."
        )

    rows = int(
        len(dataframe)
    )

    columns = int(
        len(dataframe.columns)
    )

    total_cells = (
        rows * columns
    )

    missing_cells = int(
        dataframe.isna()
        .sum()
        .sum()
    )

    duplicate_rows = int(
        dataframe.duplicated()
        .sum()
    )

    numeric_columns = int(
        len(
            dataframe.select_dtypes(
                include="number"
            ).columns
        )
    )

    categorical_columns = int(
        len(
            dataframe.select_dtypes(
                include=[
                    "object",
                    "category",
                    "string",
                ]
            ).columns
        )
    )

    datetime_columns = int(
        len(
            dataframe.select_dtypes(
                include=[
                    "datetime",
                    "datetimetz",
                ]
            ).columns
        )
    )

    # --------------------------------------------------------
    # TARGET VALIDATION
    # --------------------------------------------------------

    target_missing_values = 0

    if target:

        if target not in dataframe.columns:

            raise ValueError(
                f"Target column '{target}' "
                "does not exist in the dataset."
            )

        target_missing_values = int(
            dataframe[target]
            .isna()
            .sum()
        )

    missing_percentage = (
        (
            missing_cells
            / total_cells
        )
        * 100
        if total_cells
        else 0.0
    )

    dtype_map = {
        str(column): str(dtype)
        for column, dtype
        in dataframe.dtypes.items()
    }

    return {

        "rows": rows,

        "columns": columns,

        "target": target,

        "target_missing_values":
            target_missing_values,

        "duplicate_rows":
            duplicate_rows,

        "missing_cells":
            missing_cells,

        "missing_percentage":
            round(
                missing_percentage,
                2,
            ),

        "numeric_columns":
            numeric_columns,

        "categorical_columns":
            categorical_columns,

        "datetime_columns":
            datetime_columns,

        "column_names":
            [
                str(column)
                for column
                in dataframe.columns
            ],

        "dtypes":
            dtype_map,
    }


# ============================================================
# HEALTH
# ============================================================

@router.get(
    "/health"
)
def health() -> dict[str, Any]:
    """
    NEXUS API health check.
    """

    timestamp = (
        datetime.now()
        .isoformat()
    )

    return {

        "status":
            "healthy",

        "service":
            "NEXUS AI",

        "version":
            API_VERSION,

        "timestamp":
            timestamp,

        "details": {

            "api":
                "online",

            "analytics":
                "available",

            "reporting":
                "available",

        },
    }


# ============================================================
# API INFORMATION
# ============================================================

@router.get(
    "/"
)
def api_info() -> dict[str, Any]:
    """
    Return information about the NEXUS API.
    """

    return {

        "name":
            "NEXUS AI",

        "description":
            "Autonomous Enterprise Intelligence API",

        "version":
            API_VERSION,

        "status":
            "online",

        "endpoints": [

            "/",

            "/health",

            "/validate",

            "/analyze",

            "/report",

        ],
    }


# ============================================================
# VALIDATE DATASET
# ============================================================

@router.post(
    "/validate"
)
def validate_dataset(
    request: DatasetRequest,
) -> dict[str, Any]:
    """
    Validate a CSV dataset without running
    the complete intelligence pipeline.
    """

    try:

        dataframe = load_csv(
            request.csv_data
        )

        validation = validate_dataframe(
            dataframe,
            request.target,
        )

        return {

            "valid":
                True,

            "status":
                "valid",

            "message":
                "Dataset passed API-level validation.",

            "rows":
                validation["rows"],

            "columns":
                validation["columns"],

            "target":
                request.target,

            "details":
                validation,
        }

    except Exception as error:

        return {

            "valid":
                False,

            "status":
                "invalid",

            "message":
                str(error),

        }


# ============================================================
# ANALYZE DATASET
# ============================================================

@router.post(
    "/analyze"
)
async def analyze_dataset(
    files: list[UploadFile] | None = File(default=None),
    file: UploadFile | None = File(default=None),
    target: str | None = Form(default=None),
) -> dict[str, Any]:
    """
    Execute the complete NEXUS AI intelligence pipeline.

    Pipeline:

    CSV
      ↓
    Validation
      ↓
    Advanced Orchestrator
      ↓
    Data Quality
      ↓
    Schema Intelligence
      ↓
    Statistics
      ↓
    Correlation
      ↓
    Outliers
      ↓
    Business Metrics
      ↓
    Root Cause
      ↓
    Risk Intelligence
      ↓
    ML Readiness
      ↓
    Decision Intelligence
      ↓
    Executive Recommendations
    """

    # ----------------------------------------------------
    # MULTIPART FILE -> EXISTING DATASET REQUEST ADAPTER
    # ----------------------------------------------------

    uploads: list[UploadFile] = list(files or [])

    if file is not None:
        uploads.append(file)

    if not uploads:
        raise HTTPException(
            status_code=400,
            detail="No dataset file uploaded. Use multipart field 'files'.",
        )

    if len(uploads) > 1:
        raise HTTPException(
            status_code=400,
            detail=(
                "The current /api/analyze endpoint accepts one dataset "
                "per request. Please select one CSV file."
            ),
        )

    uploaded = uploads[0]

    content = await uploaded.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded dataset is empty.",
        )

    filename = uploaded.filename or "dataset.csv"

    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=415,
            detail="The current /api/analyze endpoint accepts CSV files.",
        )

    try:
        csv_data = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        csv_data = content.decode("latin-1")

    request = DatasetRequest(
        csv_data=csv_data,
        target=target,
        filename=filename,
    )

    start_time = time.perf_counter()

    try:

        # ----------------------------------------------------
        # LOAD
        # ----------------------------------------------------

        dataframe = load_csv(
            request.csv_data
        )

        # ----------------------------------------------------
        # VALIDATE
        # ----------------------------------------------------

        validation = validate_dataframe(
            dataframe,
            request.target,
        )

        # ----------------------------------------------------
        # ORCHESTRATOR
        # ----------------------------------------------------

        orchestrator = (
            AdvancedNexusOrchestrator()
        )

        results = (
            orchestrator.execute(
                dataframe,
                target=request.target,
            )
        )

        if not isinstance(
            results,
            dict,
        ):

            raise RuntimeError(
                "NEXUS orchestrator returned "
                "an invalid result package."
            )

        # ----------------------------------------------------
        # EXECUTION METADATA
        # ----------------------------------------------------

        execution_time = (
            time.perf_counter()
            - start_time
        )

        timestamp = (
            datetime.now()
            .isoformat()
        )

        api_metadata = {

            "execution_time_seconds":
                round(
                    execution_time,
                    6,
                ),

            "rows":
                len(dataframe),

            "columns":
                len(dataframe.columns),

            "target":
                request.target,

            "timestamp":
                timestamp,
        }

        # ----------------------------------------------------
        # FINAL RESPONSE PACKAGE
        # ----------------------------------------------------

        response_results = {

            "api_metadata":
                api_metadata,

            "validation":
                validation,

            "intelligence":
                results,
        }

        return {

            "success":
                True,

            "status":
                "success",

            "message":
                "NEXUS AI analysis completed successfully.",

            "target":
                request.target,

            "rows":
                len(dataframe),

            "columns":
                len(dataframe.columns),

            "filename":
                request.filename,

            "timestamp":
                timestamp,

            "results":
                json_safe(
                    response_results
                ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "NEXUS AI analysis failed.",

                "error":
                    str(error),
            },
        ) from error


# ============================================================
# GENERATE PDF REPORT
# ============================================================

@router.post(
    "/report"
)
def generate_pdf_report(
    request: DatasetRequest,
) -> Response:
    """
    Run NEXUS analysis and return a PDF report.
    """

    try:

        # ----------------------------------------------------
        # LOAD DATA
        # ----------------------------------------------------

        dataframe = load_csv(
            request.csv_data
        )

        # ----------------------------------------------------
        # VALIDATE
        # ----------------------------------------------------

        validate_dataframe(
            dataframe,
            request.target,
        )

        # ----------------------------------------------------
        # ANALYZE
        # ----------------------------------------------------

        orchestrator = (
            AdvancedNexusOrchestrator()
        )

        results = (
            orchestrator.execute(
                dataframe,
                target=request.target,
            )
        )

        if not isinstance(
            results,
            dict,
        ):

            raise RuntimeError(
                "Invalid NEXUS result package."
            )

        # ----------------------------------------------------
        # GENERATE PDF
        # ----------------------------------------------------

        pdf_bytes = generate_report(
            results,
            dataframe,
        )

        if not isinstance(
            pdf_bytes,
            (
                bytes,
                bytearray,
            ),
        ):

            raise RuntimeError(
                "Report generator did not "
                "return PDF bytes."
            )

        filename = (
            request.filename
            or "nexus_ai_report"
        )

        # Always use PDF extension
        if not filename.lower().endswith(
            ".pdf"
        ):

            filename = (
                filename
                .rsplit(".", 1)[0]
                + ".pdf"
            )

        else:

            filename = (
                filename
                .replace(
                    ".csv",
                    "",
                )
            )

        return Response(

            content=bytes(
                pdf_bytes
            ),

            media_type=
                "application/pdf",

            headers={
                "Content-Disposition":
                    (
                        "attachment; "
                        f'filename="{filename}"'
                    )
            },
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "PDF report generation failed.",

                "error":
                    str(error),
            },
        ) from error