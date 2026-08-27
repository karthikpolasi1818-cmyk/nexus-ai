from __future__ import annotations

import json
from typing import Any

import pandas as pd
import streamlit as st

from app.core.audit import read_audit_events
from app.core.config import settings
from app.core.health import run_health_check

try:
    from app.core.logger import (
        log_exception,
        log_info,
    )
except ImportError:

    def log_info(message: str) -> None:
        print(f"[INFO] {message}")

    def log_exception(message: str) -> None:
        print(f"[ERROR] {message}")


class SystemMonitor:
    """
    NEXUS AI System Monitoring Dashboard.

    Provides:
        - System health
        - Module health
        - Runtime information
        - Directory health
        - Audit trail
        - Configuration overview
    """

    # ========================================================
    # SAFE HELPERS
    # ========================================================

    @staticmethod
    def _safe_string(
        value: Any,
        default: str = "",
    ) -> str:
        """Safely convert a value to string."""

        if value is None:
            return default

        try:
            return str(value)

        except Exception:
            return default

    @staticmethod
    def _safe_bool(
        value: Any,
    ) -> bool:
        """Safely convert a value to bool."""

        if isinstance(value, bool):
            return value

        if isinstance(value, str):

            return value.strip().lower() in {
                "true",
                "1",
                "yes",
                "healthy",
                "available",
            }

        return bool(value)

    @staticmethod
    def _safe_json(
        value: Any,
    ) -> str:
        """Convert arbitrary values to JSON-safe text."""

        try:

            return json.dumps(
                value,
                ensure_ascii=False,
                default=str,
            )

        except Exception:

            return str(value)

    # ========================================================
    # HEALTH
    # ========================================================

    @staticmethod
    def _render_health(
        health: dict[str, Any],
    ) -> None:
        """Render overall health information."""

        status = SystemMonitor._safe_string(
            health.get(
                "status",
                "unknown",
            ),
            "unknown",
        )

        summary = health.get(
            "summary",
            {},
        )

        if not isinstance(
            summary,
            dict,
        ):
            summary = {}

        total_modules = summary.get(
            "total_modules",
            0,
        )

        healthy_modules = summary.get(
            "healthy_modules",
            0,
        )

        failed_modules = summary.get(
            "failed_modules",
            0,
        )

        failed_directories = summary.get(
            "failed_directories",
            0,
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "System Status",
            status.upper(),
        )

        c2.metric(
            "Healthy Modules",
            healthy_modules,
        )

        c3.metric(
            "Failed Modules",
            failed_modules,
        )

        c4.metric(
            "Directory Errors",
            failed_directories,
        )

        if status.lower() == "healthy":

            st.success(
                "🟢 NEXUS AI system is healthy."
            )

        elif status.lower() == "degraded":

            st.warning(
                "🟡 NEXUS AI is running in a degraded state."
            )

        else:

            st.error(
                "🔴 NEXUS AI health status is unknown."
            )

        if total_modules:

            percentage = (
                healthy_modules
                / total_modules
                * 100
            )

            st.progress(
                min(
                    max(
                        int(percentage),
                        0,
                    ),
                    100,
                )
            )

            st.caption(
                f"Module health: "
                f"{healthy_modules}/{total_modules} "
                f"({percentage:.1f}%)"
            )

    # ========================================================
    # MODULES
    # ========================================================

    @staticmethod
    def _render_modules(
        health: dict[str, Any],
    ) -> None:
        """Render module health table."""

        st.subheader(
            "🔌 Module Health"
        )

        modules = health.get(
            "modules",
            [],
        )

        if not isinstance(
            modules,
            list,
        ):
            modules = []

        rows: list[dict[str, Any]] = []

        for item in modules:

            if not isinstance(
                item,
                dict,
            ):
                continue

            module_name = SystemMonitor._safe_string(
                item.get(
                    "module",
                    "Unknown",
                ),
                "Unknown",
            )

            module_status = SystemMonitor._safe_string(
                item.get(
                    "status",
                    "unknown",
                ),
                "unknown",
            )

            error = item.get(
                "error"
            )

            rows.append(
                {
                    "Module": module_name,
                    "Status": module_status,
                    "Error": (
                        ""
                        if error is None
                        else SystemMonitor._safe_string(
                            error
                        )
                    ),
                }
            )

        if not rows:

            st.info(
                "No module health information available."
            )

            return

        dataframe = pd.DataFrame(
            rows
        )

        st.dataframe(
            dataframe,
            width="stretch",
            hide_index=True,
        )

    # ========================================================
    # RUNTIME
    # ========================================================

    @staticmethod
    def _render_runtime(
        health: dict[str, Any],
    ) -> None:
        """Render runtime environment."""

        st.subheader(
            "🐍 Runtime Environment"
        )

        python_info = health.get(
            "python",
            {},
        )

        if not isinstance(
            python_info,
            dict,
        ):
            python_info = {}

        version = SystemMonitor._safe_string(
            python_info.get(
                "version",
                "Unknown",
            ),
            "Unknown",
        )

        status = SystemMonitor._safe_string(
            python_info.get(
                "status",
                "Unknown",
            ),
            "Unknown",
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Python Version",
            version,
        )

        c2.metric(
            "Runtime Status",
            status.upper(),
        )

    # ========================================================
    # DIRECTORIES
    # ========================================================

    @staticmethod
    def _render_directories(
        health: dict[str, Any],
    ) -> None:
        """Render directory health."""

        st.subheader(
            "📁 Project Directories"
        )

        directories = health.get(
            "directories",
            {},
        )

        if not isinstance(
            directories,
            dict,
        ):
            directories = {}

        rows: list[dict[str, Any]] = []

        for name, info in directories.items():

            if not isinstance(
                info,
                dict,
            ):
                info = {}

            rows.append(
                {
                    "Directory": SystemMonitor._safe_string(
                        name
                    ),
                    "Path": SystemMonitor._safe_string(
                        info.get(
                            "path",
                            "",
                        )
                    ),
                    "Exists": SystemMonitor._safe_bool(
                        info.get(
                            "exists",
                            False,
                        )
                    ),
                    "Status": SystemMonitor._safe_string(
                        info.get(
                            "status",
                            "unknown",
                        ),
                        "unknown",
                    ),
                }
            )

        if not rows:

            st.info(
                "No directory information available."
            )

            return

        dataframe = pd.DataFrame(
            rows
        )

        st.dataframe(
            dataframe,
            width="stretch",
            hide_index=True,
        )

    # ========================================================
    # AUDIT
    # ========================================================

    @staticmethod
    def _render_audit() -> None:
        """Render recent audit events."""

        st.subheader(
            "📜 Recent Audit Events"
        )

        try:

            events = read_audit_events(
                limit=50
            )

        except Exception as error:

            log_exception(
                f"Unable to read audit events: {error}"
            )

            st.error(
                "Unable to load audit events."
            )

            return

        if not events:

            st.info(
                "No audit events recorded yet."
            )

            return

        rows: list[dict[str, Any]] = []

        for event in reversed(events):

            if not isinstance(
                event,
                dict,
            ):
                continue

            details = event.get(
                "details",
                {},
            )

            rows.append(
                {
                    "Timestamp": SystemMonitor._safe_string(
                        event.get(
                            "timestamp",
                            "",
                        )
                    ),
                    "Event": SystemMonitor._safe_string(
                        event.get(
                            "event",
                            "",
                        )
                    ),
                    "Status": SystemMonitor._safe_string(
                        event.get(
                            "status",
                            "",
                        )
                    ),
                    "Details": SystemMonitor._safe_json(
                        details
                    ),
                }
            )

        if not rows:

            st.info(
                "No valid audit events found."
            )

            return

        dataframe = pd.DataFrame(
            rows
        )

        st.dataframe(
            dataframe,
            width="stretch",
            hide_index=True,
        )

    # ========================================================
    # CONFIGURATION
    # ========================================================

    @staticmethod
    def _render_configuration() -> None:
        """Render current NEXUS configuration."""

        with st.expander(
            "⚙️ NEXUS Configuration",
            expanded=False,
        ):

            configuration = {
                "Application": getattr(
                    settings,
                    "APP_NAME",
                    "NEXUS AI",
                ),
                "Version": getattr(
                    settings,
                    "APP_VERSION",
                    "Unknown",
                ),
                "Environment": getattr(
                    settings,
                    "ENVIRONMENT",
                    "development",
                ),
                "Log Level": getattr(
                    settings,
                    "LOG_LEVEL",
                    "INFO",
                ),
                "Max Preview Rows": getattr(
                    settings,
                    "MAX_PREVIEW_ROWS",
                    100,
                ),
                "Max Report Rows": getattr(
                    settings,
                    "MAX_REPORT_ROWS",
                    10000,
                ),
                "Data Directory": str(
                    getattr(
                        settings,
                        "DATA_DIR",
                        "",
                    )
                ),
                "Log Directory": str(
                    getattr(
                        settings,
                        "LOG_DIR",
                        "",
                    )
                ),
                "Report Directory": str(
                    getattr(
                        settings,
                        "REPORT_DIR",
                        "",
                    )
                ),
            }

            dataframe = pd.DataFrame(
                {
                    "Setting": list(
                        configuration.keys()
                    ),
                    "Value": [
                        SystemMonitor._safe_string(
                            value
                        )
                        for value in configuration.values()
                    ],
                }
            )

            st.dataframe(
                dataframe,
                width="stretch",
                hide_index=True,
            )

    # ========================================================
    # MAIN RENDER
    # ========================================================

    @classmethod
    def render(cls) -> None:
        """Render complete system monitoring interface."""

        st.header(
            "🖥️ NEXUS System Monitor"
        )

        st.caption(
            "Real-time health, runtime, audit, "
            "and configuration monitoring."
        )

        # ----------------------------------------------------
        # REFRESH
        # ----------------------------------------------------

        refresh = st.button(
            "🔄 Refresh System Status",
            key="nexus_system_monitor_refresh",
        )

        if refresh:

            try:

                st.rerun()

            except Exception:

                pass

        # ----------------------------------------------------
        # HEALTH CHECK
        # ----------------------------------------------------

        try:

            health = run_health_check()

        except Exception as error:

            log_exception(
                f"System health check failed: {error}"
            )

            st.error(
                "❌ System health check failed."
            )

            return

        if not isinstance(
            health,
            dict,
        ):

            st.error(
                "❌ Invalid health-check response."
            )

            return

        log_info(
            "System Monitor rendered successfully."
        )

        # ----------------------------------------------------
        # SECTIONS
        # ----------------------------------------------------

        cls._render_health(
            health
        )

        st.divider()

        cls._render_modules(
            health
        )

        st.divider()

        cls._render_runtime(
            health
        )

        st.divider()

        cls._render_directories(
            health
        )

        st.divider()

        cls._render_audit()

        st.divider()

        cls._render_configuration()


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================

def render_system_monitor() -> None:
    """Convenience wrapper."""

    SystemMonitor.render()