from __future__ import annotations

from app.core.exceptions import (
    NexusError,
    NexusDataError,
    NexusDataLoadError,
    NexusDataValidationError,
    NexusAnalyticsError,
    NexusInsightError,
    NexusDecisionError,
    NexusOrchestrationError,
    NexusReportError,
    NexusConfigurationError,
    NexusConfigurationLoadError,
    NexusExportError,
    NexusSystemError,
    NexusHealthCheckError,
    NexusAuditError,
    NexusApplicationError,
    is_nexus_error,
    exception_to_dict,
    get_error_code,
    get_error_message,
)


# ============================================================
# BASE EXCEPTION
# ============================================================

def test_nexus_error():
    error = NexusError(
        "Something went wrong"
    )

    assert error.code == "NEXUS_ERROR"
    assert error.message == "Something went wrong"
    assert str(error) == (
        "[NEXUS_ERROR] Something went wrong"
    )


# ============================================================
# ERROR CODES
# ============================================================

def test_data_error_codes():

    assert NexusDataError(
        "Data error"
    ).code == "DATA_ERROR"

    assert NexusDataLoadError(
        "Load error"
    ).code == "DATA_LOAD_ERROR"

    assert NexusDataValidationError(
        "Validation error"
    ).code == "DATA_VALIDATION_ERROR"


def test_analytics_error_codes():

    assert NexusAnalyticsError(
        "Analytics error"
    ).code == "ANALYTICS_ERROR"

    assert NexusInsightError(
        "Insight error"
    ).code == "INSIGHT_ERROR"

    assert NexusDecisionError(
        "Decision error"
    ).code == "DECISION_ERROR"


def test_pipeline_error_codes():

    assert NexusOrchestrationError(
        "Orchestration error"
    ).code == "ORCHESTRATION_ERROR"

    assert NexusReportError(
        "Report error"
    ).code == "REPORT_ERROR"

    assert NexusExportError(
        "Export error"
    ).code == "EXPORT_ERROR"


def test_system_error_codes():

    assert NexusConfigurationError(
        "Configuration error"
    ).code == "CONFIGURATION_ERROR"

    assert NexusConfigurationLoadError(
        "Configuration load error"
    ).code == "CONFIGURATION_LOAD_ERROR"

    assert NexusSystemError(
        "System error"
    ).code == "SYSTEM_ERROR"

    assert NexusHealthCheckError(
        "Health check error"
    ).code == "HEALTH_CHECK_ERROR"

    assert NexusAuditError(
        "Audit error"
    ).code == "AUDIT_ERROR"

    assert NexusApplicationError(
        "Application error"
    ).code == "APPLICATION_ERROR"


# ============================================================
# INHERITANCE
# ============================================================

def test_exception_inheritance():

    assert isinstance(
        NexusDataError("x"),
        NexusError,
    )

    assert isinstance(
        NexusDataLoadError("x"),
        NexusDataError,
    )

    assert isinstance(
        NexusInsightError("x"),
        NexusAnalyticsError,
    )

    assert isinstance(
        NexusDecisionError("x"),
        NexusAnalyticsError,
    )

    assert isinstance(
        NexusReportError("x"),
        NexusError,
    )


# ============================================================
# DETAILS
# ============================================================

def test_exception_details():

    error = NexusDataValidationError(
        "Invalid dataset",
        details={
            "rows": 0,
            "column": "Sales",
        },
    )

    assert error.details["rows"] == 0
    assert error.details["column"] == "Sales"


# ============================================================
# DICTIONARY SERIALIZATION
# ============================================================

def test_exception_to_dict():

    error = NexusDataValidationError(
        "Invalid dataset",
        details={
            "rows": 0,
            "columns": 4,
        },
    )

    result = error.to_dict()

    assert result["success"] is False
    assert result["error"] == (
        "DATA_VALIDATION_ERROR"
    )
    assert result["error_type"] == (
        "NexusDataValidationError"
    )
    assert result["message"] == (
        "Invalid dataset"
    )

    assert result["details"]["rows"] == 0


# ============================================================
# JSON-SAFE DETAILS
# ============================================================

def test_nested_details_are_safe():

    error = NexusError(
        "Test",
        details={
            "items": [
                1,
                2,
                3,
            ],
            "nested": {
                "value": "ok",
            },
        },
    )

    result = error.to_dict()

    assert result["details"]["items"] == [
        1,
        2,
        3,
    ]

    assert result["details"]["nested"]["value"] == (
        "ok"
    )


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def test_is_nexus_error():

    nexus_error = NexusError(
        "NEXUS error"
    )

    normal_error = ValueError(
        "Normal error"
    )

    assert is_nexus_error(
        nexus_error
    ) is True

    assert is_nexus_error(
        normal_error
    ) is False


def test_exception_to_dict_for_normal_exception():

    error = ValueError(
        "Something failed"
    )

    result = exception_to_dict(
        error
    )

    assert result["success"] is False
    assert result["error"] == (
        "INTERNAL_ERROR"
    )
    assert result["error_type"] == (
        "ValueError"
    )
    assert result["message"] == (
        "Something failed"
    )


def test_get_error_code():

    nexus_error = NexusInsightError(
        "Insight failed"
    )

    normal_error = RuntimeError(
        "Runtime failed"
    )

    assert get_error_code(
        nexus_error
    ) == "INSIGHT_ERROR"

    assert get_error_code(
        normal_error
    ) == "INTERNAL_ERROR"


def test_get_error_message():

    error = NexusReportError(
        "Report failed"
    )

    assert get_error_message(
        error
    ) == (
        "[REPORT_ERROR] Report failed"
    )


# ============================================================
# REPRESENTATION
# ============================================================

def test_error_repr():

    error = NexusError(
        "Test error",
        details={
            "source": "test"
        },
    )

    representation = repr(
        error
    )

    assert "NexusError" in representation
    assert "Test error" in representation
    assert "NEXUS_ERROR" in representation