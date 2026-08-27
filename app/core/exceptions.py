from __future__ import annotations

from typing import Any


# ============================================================
# NEXUS AI EXCEPTION SYSTEM
# ============================================================


class NexusError(Exception):
    """
    Base exception for NEXUS AI.

    All custom NEXUS exceptions inherit from this class.

    Features:
        - Stable error code
        - Human-readable message
        - Optional structured details
        - JSON-safe serialization
        - Clean string representation
    """

    def __init__(
        self,
        message: str,
        *,
        code: str = "NEXUS_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:

        self.message = str(message)

        self.code = str(
            code
        )

        self.details = (
            details.copy()
            if isinstance(
                details,
                dict,
            )
            else {}
        )

        super().__init__(
            self.message
        )

    # ========================================================
    # STRING REPRESENTATION
    # ========================================================

    def __str__(
        self,
    ) -> str:

        return (
            f"[{self.code}] "
            f"{self.message}"
        )

    def __repr__(
        self,
    ) -> str:

        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"code={self.code!r}, "
            f"details={self.details!r}"
            f")"
        )

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Convert exception into a
        JSON-friendly dictionary.
        """

        return {
            "success": False,
            "error": self.code,
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self._json_safe(
                self.details
            ),
        }

    def to_json_safe(
        self,
    ) -> dict[str, Any]:
        """
        Alias for to_dict().
        """

        return self.to_dict()

    # ========================================================
    # SAFE CONVERSION
    # ========================================================

    @staticmethod
    def _json_safe(
        value: Any,
    ) -> Any:
        """
        Recursively convert arbitrary
        Python objects into JSON-safe values.
        """

        if value is None:

            return None

        if isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
            ),
        ):

            return value

        if isinstance(
            value,
            dict,
        ):

            return {
                str(key): NexusError._json_safe(
                    item
                )
                for key, item in value.items()
            }

        if isinstance(
            value,
            (
                list,
                tuple,
                set,
            ),
        ):

            return [
                NexusError._json_safe(
                    item
                )
                for item in value
            ]

        try:

            return str(value)

        except Exception:

            return repr(value)


# ============================================================
# DATA ERRORS
# ============================================================


class NexusDataError(
    NexusError
):
    """
    Dataset loading, validation,
    schema, or data-quality error.
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:

        super().__init__(
            message,
            code="DATA_ERROR",
            details=details,
        )


class NexusDataLoadError(
    NexusDataError
):
    """
    Dataset could not be loaded.
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:

        NexusError.__init__(
            self,
            message,
            code="DATA_LOAD_ERROR",
            details=details,
        )


class NexusDataValidationError(
    NexusDataError
):
    """
    Dataset failed validation.
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:

        NexusError.__init__(
            self,
            message,
            code="DATA_VALIDATION_ERROR",
            details=details,
        )


# ============================================================
# ANALYTICS ERRORS
# ============================================================


class NexusAnalyticsError(
    NexusError
):
    """
    General analytics engine failure.
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:

        super().__init__(
            message,
            code="ANALYTICS_ERROR",
            details=details,
        )


class NexusInsightError(
    NexusAnalyticsError
):
    """
    Insight engine failure.
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:

        NexusError.__init__(
            self,
            message,
            code="INSIGHT_ERROR",
            details=details,
        )


class NexusDecisionError(
    NexusAnalyticsError
):
    """
    Decision intelligence failure.
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:

        NexusError.__init__(
            self,
            message,
            code="DECISION_ERROR",
            details=details,
        )


# ============================================================
# ORCHESTRATION ERRORS
# ============================================================


class NexusOrchestrationError(
    NexusError
):
    """
    Failure in the autonomous
    orchestration pipeline.
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:

        super().__init__(
            message,
            code="ORCHESTRATION_ERROR",
            details=details,
        )


# ============================================================
# REPORT ERRORS
# ============================================================


class NexusReportError(
    NexusError
):
    """
    PDF/report generation failure.
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:

        super().__init__(
            message,
            code="REPORT_ERROR",
            details=details,
        )


# ============================================================
# CONFIGURATION ERRORS
# ============================================================


class NexusConfigurationError(
    NexusError
):
    """
    Application configuration error.
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:

        super().__init__(
            message,
            code="CONFIGURATION_ERROR",
            details=details,
        )


# ============================================================
# EXPORT ERRORS
# ============================================================


class NexusExportError(
    NexusError
):
    """
    Export/download generation failure.
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:

        super().__init__(
            message,
            code="EXPORT_ERROR",
            details=details,
        )


# ============================================================
# SYSTEM ERRORS
# ============================================================


class NexusSystemError(
    NexusError
):
    """
    General infrastructure/system failure.
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:

        super().__init__(
            message,
            code="SYSTEM_ERROR",
            details=details,
        )


class NexusConfigurationLoadError(
    NexusConfigurationError
):
    """
    Configuration could not be loaded.
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:

        NexusError.__init__(
            self,
            message,
            code="CONFIGURATION_LOAD_ERROR",
            details=details,
        )


class NexusHealthCheckError(
    NexusSystemError
):
    """
    System health check failure.
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:

        NexusError.__init__(
            self,
            message,
            code="HEALTH_CHECK_ERROR",
            details=details,
        )


class NexusAuditError(
    NexusSystemError
):
    """
    Audit logging failure.
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:

        NexusError.__init__(
            self,
            message,
            code="AUDIT_ERROR",
            details=details,
        )


# ============================================================
# APPLICATION ERRORS
# ============================================================


class NexusApplicationError(
    NexusError
):
    """
    General application-level failure.
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:

        super().__init__(
            message,
            code="APPLICATION_ERROR",
            details=details,
        )


# ============================================================
# ERROR UTILITIES
# ============================================================


def is_nexus_error(
    error: BaseException,
) -> bool:
    """
    Check whether an exception belongs
    to the NEXUS exception hierarchy.
    """

    return isinstance(
        error,
        NexusError,
    )


def exception_to_dict(
    error: BaseException,
) -> dict[str, Any]:
    """
    Convert any exception into a
    JSON-safe dictionary.
    """

    if isinstance(
        error,
        NexusError,
    ):

        return error.to_dict()

    return {
        "success": False,
        "error": "INTERNAL_ERROR",
        "error_type": type(
            error
        ).__name__,
        "message": str(error),
        "details": {},
    }


def get_error_code(
    error: BaseException,
) -> str:
    """
    Return the NEXUS error code.
    """

    if isinstance(
        error,
        NexusError,
    ):

        return error.code

    return "INTERNAL_ERROR"


def get_error_message(
    error: BaseException,
) -> str:
    """
    Return a safe human-readable message.
    """

    try:

        return str(error)

    except Exception:

        return (
            "An unexpected error occurred."
        )


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "NexusError",
    "NexusDataError",
    "NexusDataLoadError",
    "NexusDataValidationError",
    "NexusAnalyticsError",
    "NexusInsightError",
    "NexusDecisionError",
    "NexusOrchestrationError",
    "NexusReportError",
    "NexusConfigurationError",
    "NexusConfigurationLoadError",
    "NexusExportError",
    "NexusSystemError",
    "NexusHealthCheckError",
    "NexusAuditError",
    "NexusApplicationError",
    "is_nexus_error",
    "exception_to_dict",
    "get_error_code",
    "get_error_message",
]