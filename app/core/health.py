from __future__ import annotations

import importlib
import sys
from datetime import datetime
from typing import Any

from app.core.config import settings
from app.core.logger import (
    log_exception,
    log_info,
)


# ============================================================
# NEXUS AI — REQUIRED BACKEND MODULES
# ============================================================
#
# IMPORTANT:
# Do NOT include "app.main" here.
#
# app.main is the Streamlit application entry point.
# Importing it executes the Streamlit UI and creates widgets
# such as st.file_uploader(), st.sidebar, st.title(), etc.
#
# The health checker itself is called from app.main, so importing
# app.main from here creates a circular UI execution:
#
#     app.main
#        ↓
#     run_health_check()
#        ↓
#     import app.main
#        ↓
#     Streamlit widgets created again
#        ↓
#     DuplicateElementId
#
# Therefore only backend/supporting modules are checked here.
# ============================================================

REQUIRED_MODULES = [
    "app.agents.advanced_orchestrator",
    "app.analytics.advanced_intelligence",
    "app.analytics.insight_engine",
    "app.analytics.decision_engine",
    "app.analytics.decision_intelligence",
    "app.ui.advanced_panels",
    "app.ui.insight_panel",
    "app.ui.copilot_panel",
    "app.services.data_loader",
    "app.services.report_generator",
]


# ============================================================
# MODULE HEALTH CHECK
# ============================================================


def check_module(
    module_name: str,
) -> dict[str, Any]:
    """
    Check whether a Python module can be imported successfully.

    The Streamlit entry point app.main is intentionally excluded
    from REQUIRED_MODULES to prevent UI execution during health
    checks.
    """

    try:
        importlib.import_module(
            module_name
        )

        return {
            "module": module_name,
            "status": "healthy",
            "error": None,
        }

    except Exception as error:

        log_exception(
            f"Health check failed for "
            f"{module_name}: {error}"
        )

        return {
            "module": module_name,
            "status": "failed",
            "error": str(error),
        }


# ============================================================
# PYTHON VERSION CHECK
# ============================================================


def check_python() -> dict[str, Any]:
    """
    Verify that the running Python version
    is supported by NEXUS AI.
    """

    version = sys.version.split()[0]

    supported = (
        sys.version_info >= (3, 10)
    )

    return {
        "version": version,
        "status": (
            "healthy"
            if supported
            else "unsupported"
        ),
    }


# ============================================================
# DIRECTORY CHECK
# ============================================================


def check_directories() -> dict[str, Any]:
    """
    Verify that all required NEXUS directories exist.
    """

    directories = {
        "data": settings.DATA_DIR,
        "logs": settings.LOG_DIR,
        "reports": settings.REPORT_DIR,
        "tests": settings.TEST_DIR,
    }

    checks: dict[str, Any] = {}

    for name, path in directories.items():

        exists = path.exists()

        checks[name] = {
            "path": str(path),
            "exists": exists,
            "status": (
                "healthy"
                if exists
                else "missing"
            ),
        }

    return checks


# ============================================================
# HEALTH CHECK
# ============================================================


def run_health_check() -> dict[str, Any]:
    """
    Run the complete NEXUS system health check.

    Checks:

    1. Python runtime
    2. Required backend modules
    3. Required directories

    The Streamlit application entry point is deliberately not
    imported here.
    """

    started = datetime.now()

    log_info(
        "Running NEXUS system health check."
    )

    # --------------------------------------------------------
    # MODULE CHECKS
    # --------------------------------------------------------

    module_checks = [
        check_module(module)
        for module in REQUIRED_MODULES
    ]

    failed_modules = [
        item
        for item in module_checks
        if item["status"] != "healthy"
    ]

    # --------------------------------------------------------
    # DIRECTORY CHECKS
    # --------------------------------------------------------

    directory_checks = (
        check_directories()
    )

    failed_directories = [
        item
        for item in directory_checks.values()
        if item["status"] != "healthy"
    ]

    # --------------------------------------------------------
    # PYTHON CHECK
    # --------------------------------------------------------

    python_check = check_python()

    # --------------------------------------------------------
    # OVERALL STATUS
    # --------------------------------------------------------

    overall_healthy = (
        not failed_modules
        and not failed_directories
        and python_check["status"]
        == "healthy"
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    result: dict[str, Any] = {
        "status": (
            "healthy"
            if overall_healthy
            else "degraded"
        ),
        "timestamp": started.isoformat(),
        "python": python_check,
        "modules": module_checks,
        "directories": directory_checks,
        "summary": {
            "total_modules": len(
                module_checks
            ),
            "healthy_modules": (
                len(module_checks)
                - len(failed_modules)
            ),
            "failed_modules": len(
                failed_modules
            ),
            "healthy_directories": (
                len(directory_checks)
                - len(failed_directories)
            ),
            "failed_directories": len(
                failed_directories
            ),
        },
    }

    # --------------------------------------------------------
    # LOG RESULT
    # --------------------------------------------------------

    log_info(
        "NEXUS health check completed | "
        f"status={result['status']}"
    )

    return result