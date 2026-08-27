from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from app.agents.advanced_orchestrator import (
    AdvancedNexusOrchestrator,
)
from app.analytics.insight_engine import (
    InsightEngine,
)
from app.core.audit import audit_event
from app.core.config import settings
from app.core.data_validator import (
    DataValidator,
)
from app.core.exceptions import (
    NexusDataValidationError,
)
from app.core.health import run_health_check
from app.ui.advanced_panels import (
    AdvancedPanels,
)
from app.ui.insight_panel import (
    InsightPanel,
)


# ============================================================
# OPTIONAL SYSTEM MONITOR
# ============================================================

try:

    from app.ui.system_monitor import (
        SystemMonitor,
    )

except ImportError:

    SystemMonitor = None


# ============================================================
# LOGGER
# ============================================================

try:

    from app.core.logger import (
        log_error,
        log_exception,
        log_info,
    )

except ImportError:

    def log_info(
        message: str,
    ) -> None:

        print(
            f"[INFO] {message}"
        )

    def log_error(
        message: str,
    ) -> None:

        print(
            f"[ERROR] {message}"
        )

    def log_exception(
        message: str,
    ) -> None:

        print(
            f"[ERROR] {message}"
        )


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="NEXUS AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# APPLICATION CONSTANTS
# ============================================================

APP_NAME = getattr(
    settings,
    "APP_NAME",
    "NEXUS AI",
)

APP_VERSION = getattr(
    settings,
    "APP_VERSION",
    "4.0",
)

MAX_PREVIEW_ROWS = getattr(
    settings,
    "MAX_PREVIEW_ROWS",
    100,
)

MAX_REPORT_ROWS = getattr(
    settings,
    "MAX_REPORT_ROWS",
    10000,
)


# ============================================================
# SAFE HELPERS
# ============================================================

def safe_string(
    value: Any,
    default: str = "",
) -> str:
    """
    Safely convert any value to string.
    """

    if value is None:
        return default

    try:

        return str(
            value
        )

    except Exception:

        return default


def json_safe(
    value: Any,
) -> Any:
    """
    Recursively convert values into
    JSON-safe structures.
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
            str(key): json_safe(
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
            json_safe(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        pd.DataFrame,
    ):

        return json_safe(
            value.to_dict(
                orient="records"
            )
        )

    if isinstance(
        value,
        pd.Series,
    ):

        return json_safe(
            value.to_dict()
        )

    try:

        if pd.isna(value):

            return None

    except Exception:

        pass

    try:

        return str(
            value
        )

    except Exception:

        return repr(
            value
        )


def safe_json_string(
    value: Any,
) -> str:
    """
    Convert arbitrary Python objects
    to readable JSON text.
    """

    try:

        return json.dumps(
            json_safe(
                value
            ),
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    except Exception:

        return str(
            value
        )


# ============================================================
# STREAMLIT / ARROW DATAFRAME SAFETY
# ============================================================

def dataframe_arrow_safe(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Convert mixed object columns into
    Arrow-compatible values.

    This prevents errors such as:

        ArrowInvalid:
        tried to convert DataFrame to double
    """

    if not isinstance(
        dataframe,
        pd.DataFrame,
    ):

        return pd.DataFrame()

    result = dataframe.copy()

    for column in result.columns:

        series = result[column]

        if pd.api.types.is_object_dtype(
            series.dtype
        ):

            result[column] = series.map(
                lambda value: (
                    safe_json_string(
                        value
                    )
                    if isinstance(
                        value,
                        (
                            dict,
                            list,
                            tuple,
                            set,
                            pd.DataFrame,
                            pd.Series,
                        ),
                    )
                    else safe_string(
                        value
                    )
                )
            )

    return result


def display_dataframe(
    dataframe: pd.DataFrame,
    *,
    max_rows: int | None = None,
) -> None:
    """
    Safely display a DataFrame.
    """

    if not isinstance(
        dataframe,
        pd.DataFrame,
    ):

        st.info(
            "No tabular data available."
        )

        return

    if dataframe.empty:

        st.info(
            "The DataFrame is empty."
        )

        return

    safe_df = dataframe_arrow_safe(
        dataframe
    )

    if max_rows is not None:

        safe_df = safe_df.head(
            max_rows
        )

    st.dataframe(
        safe_df,
        width="stretch",
        hide_index=True,
    )


# ============================================================
# RESULT NORMALIZATION
# ============================================================

def normalize_results(
    results: Any,
) -> dict[str, Any]:
    """
    Guarantee that analysis results
    are represented as a dictionary.
    """

    if isinstance(
        results,
        dict,
    ):

        return results

    return {
        "status": "warning",
        "message": (
            "The analysis engine returned "
            "an unexpected result format."
        ),
        "raw_result": json_safe(
            results
        ),
    }


# ============================================================
# SESSION STATE
# ============================================================

def initialize_session_state() -> None:
    """
    Initialize all NEXUS session state values.
    """

    defaults = {
        "analysis_results": None,
        "analysis_dataframe": None,
        "analysis_target": None,
        "analysis_completed": False,
        "uploaded_filename": None,
        "analysis_timestamp": None,
        "last_error": None,
        "validation_results": None,
    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[
                key
            ] = value


initialize_session_state()


# ============================================================
# HEADER
# ============================================================

st.title(
    "🧠 NEXUS AI"
)

st.caption(
    "Autonomous Enterprise Intelligence"
)

st.markdown(
    f"""
**Version:** `{APP_VERSION}`  
**Environment:** `{getattr(settings, "ENVIRONMENT", "development")}`
"""
)

st.divider()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "⚙️ NEXUS Control Center"
    )

    st.subheader(
        "📁 Dataset"
    )

    uploaded_file = st.file_uploader(
        "Upload CSV file",
        type=[
            "csv",
        ],
        help=(
            "Upload a CSV dataset "
            "for NEXUS AI analysis."
        ),
    )

    st.divider()

    st.subheader(
        "🎯 Analysis Settings"
    )

    target_column = None

    if uploaded_file is not None:

        try:

            uploaded_file.seek(
                0
            )

            preview_df = pd.read_csv(
                uploaded_file
            )

            if not preview_df.empty:

                columns = list(
                    preview_df.columns
                )

                numeric_columns = list(
                    preview_df.select_dtypes(
                        include="number"
                    ).columns
                )

                default_target = (
                    numeric_columns[0]
                    if numeric_columns
                    else columns[0]
                )

                target_column = st.selectbox(
                    "Target column",
                    options=columns,
                    index=columns.index(
                        default_target
                    ),
                )

        except Exception as error:

            st.error(
                "Unable to inspect uploaded CSV."
            )

            log_exception(
                f"CSV preview failed: {error}"
            )

    st.divider()

    st.subheader(
        "🖥️ System"
    )

    show_monitor = st.checkbox(
        "Show System Monitor",
        value=False,
    )

    st.divider()

    if st.button(
        "🗑️ Clear Analysis",
        use_container_width=True,
    ):

        st.session_state.analysis_results = None
        st.session_state.analysis_dataframe = None
        st.session_state.analysis_target = None
        st.session_state.analysis_completed = False
        st.session_state.uploaded_filename = None
        st.session_state.analysis_timestamp = None
        st.session_state.last_error = None
        st.session_state.validation_results = None

        audit_event(
            "analysis_cleared",
            details={
                "source": "sidebar",
            },
        )

        st.rerun()


# ============================================================
# SYSTEM HEALTH
# ============================================================

try:

    health = run_health_check()

except Exception as error:

    health = {
        "status": "unknown",
        "error": str(error),
    }

    log_exception(
        f"Startup health check failed: {error}"
    )


health_status = safe_string(
    health.get(
        "status",
        "unknown",
    ),
    "unknown",
).lower()


if health_status == "healthy":

    st.success(
        "🟢 NEXUS System Healthy"
    )

elif health_status == "degraded":

    st.warning(
        "🟡 NEXUS System Degraded"
    )

else:

    st.error(
        "🔴 NEXUS System Status Unknown"
    )


# ============================================================
# SYSTEM MONITOR
# ============================================================

if show_monitor:

    st.divider()

    if SystemMonitor is not None:

        try:

            SystemMonitor.render()

        except Exception as error:

            log_exception(
                f"System Monitor failed: {error}"
            )

            st.error(
                "System Monitor is currently unavailable."
            )

    else:

        st.warning(
            "System Monitor module is not available."
        )


# ============================================================
# DATA UPLOAD
# ============================================================

if uploaded_file is not None:

    try:

        uploaded_file.seek(
            0
        )

        dataframe = pd.read_csv(
            uploaded_file
        )

        if dataframe.empty:

            st.error(
                "❌ The uploaded CSV contains no rows."
            )

            audit_event(
                "dataset_empty",
                status="failed",
                details={
                    "filename": uploaded_file.name,
                },
            )

        else:

            st.session_state.analysis_dataframe = (
                dataframe.copy()
            )

            st.session_state.uploaded_filename = (
                uploaded_file.name
            )

            st.subheader(
                "📊 Dataset Preview"
            )

            metric_1, metric_2, metric_3, metric_4 = (
                st.columns(4)
            )

            metric_1.metric(
                "Rows",
                len(dataframe),
            )

            metric_2.metric(
                "Columns",
                len(dataframe.columns),
            )

            metric_3.metric(
                "Numeric Columns",
                len(
                    dataframe.select_dtypes(
                        include="number"
                    ).columns
                ),
            )

            metric_4.metric(
                "Missing Values",
                int(
                    dataframe.isna()
                    .sum()
                    .sum()
                ),
            )

            display_dataframe(
                dataframe,
                max_rows=MAX_PREVIEW_ROWS,
            )

            audit_event(
                "dataset_loaded",
                details={
                    "filename": uploaded_file.name,
                    "rows": len(dataframe),
                    "columns": len(dataframe.columns),
                },
            )

    except Exception as error:

        st.error(
            f"❌ Failed to load dataset: {error}"
        )

        st.session_state.last_error = (
            str(error)
        )

        audit_event(
            "dataset_load_failed",
            status="failed",
            details={
                "filename": uploaded_file.name,
                "error": str(error),
            },
        )

        log_exception(
            f"Dataset loading failed: {error}"
        )


# ============================================================
# ANALYSIS BUTTON
# ============================================================

st.divider()

run_analysis = st.button(
    "🚀 Run NEXUS AI Analysis",
    type="primary",
    use_container_width=True,
)


if run_analysis:

    dataframe = st.session_state.get(
        "analysis_dataframe"
    )

    filename = st.session_state.get(
        "uploaded_filename"
    )

    # --------------------------------------------------------
    # INPUT CHECK
    # --------------------------------------------------------

    if not isinstance(
        dataframe,
        pd.DataFrame,
    ):

        st.error(
            "❌ Please upload a CSV dataset first."
        )

    elif dataframe.empty:

        st.error(
            "❌ The dataset is empty."
        )

    elif not target_column:

        st.error(
            "❌ Please select a target column."
        )

    else:

        progress = st.progress(
            0
        )

        status_box = st.empty()

        try:

            # =================================================
            # VALIDATION
            # =================================================

            status_box.info(
                "🔎 Validating dataset..."
            )

            progress.progress(
                10
            )

            validation = (
                DataValidator.validate_for_analysis(
                    dataframe,
                    target_column,
                )
            )

            st.session_state.validation_results = (
                json_safe(
                    validation
                )
            )

            if not validation.get(
                "valid",
                False,
            ):

                raise NexusDataValidationError(
                    validation.get(
                        "message",
                        "Dataset validation failed.",
                    ),
                    details=validation,
                )

            validation_status = validation.get(
                "status",
                "healthy",
            )

            if validation_status == "warning":

                st.warning(
                    "⚠️ Dataset passed validation "
                    "with warnings."
                )

            else:

                st.success(
                    "✅ Dataset validation passed."
                )

            audit_event(
                "dataset_validation_completed",
                details={
                    "filename": filename,
                    "rows": len(dataframe),
                    "columns": len(dataframe.columns),
                    "target": target_column,
                    "status": validation_status,
                },
            )

            # =================================================
            # ANALYSIS START
            # =================================================

            audit_event(
                "analysis_started",
                details={
                    "filename": filename,
                    "rows": len(dataframe),
                    "columns": len(dataframe.columns),
                    "target": target_column,
                },
            )

            status_box.info(
                "🧠 Running autonomous intelligence pipeline..."
            )

            progress.progress(
                25
            )

            # =================================================
            # ORCHESTRATOR
            # =================================================

            orchestrator = (
                AdvancedNexusOrchestrator()
            )

            results = orchestrator.execute(
                dataframe,
                target=target_column,
            )

            results = normalize_results(
                results
            )

            # -------------------------------------------------
            # ADD VALIDATION INFORMATION
            # -------------------------------------------------

            results[
                "validation"
            ] = json_safe(
                validation
            )

            progress.progress(
                65
            )

            # =================================================
            # INSIGHT ENGINE
            # =================================================

            status_box.info(
                "💡 Generating business insights..."
            )

            try:

                insights = InsightEngine.generate(
                    dataframe
                )

                results[
                    "insights"
                ] = json_safe(
                    insights
                )

            except Exception as error:

                log_exception(
                    f"Insight generation failed: {error}"
                )

                results[
                    "insights"
                ] = {
                    "status": "warning",
                    "error": str(error),
                }

            progress.progress(
                80
            )

            # =================================================
            # FINALIZE RESULTS
            # =================================================

            results = normalize_results(
                results
            )

            st.session_state.analysis_results = (
                results
            )

            st.session_state.analysis_target = (
                target_column
            )

            st.session_state.analysis_completed = (
                True
            )

            st.session_state.analysis_timestamp = (
                datetime.now().isoformat()
            )

            st.session_state.last_error = None

            progress.progress(
                100
            )

            status_box.success(
                "✅ NEXUS AI analysis completed successfully."
            )

            audit_event(
                "analysis_completed",
                details={
                    "filename": filename,
                    "rows": len(dataframe),
                    "columns": len(dataframe.columns),
                    "target": target_column,
                    "validation_status": validation_status,
                    "result_keys": list(
                        results.keys()
                    ),
                },
            )

            log_info(
                "NEXUS analysis completed successfully."
            )

        # =====================================================
        # VALIDATION ERROR
        # =====================================================

        except NexusDataValidationError as error:

            progress.empty()
            status_box.empty()

            st.session_state.analysis_completed = (
                False
            )

            st.session_state.last_error = (
                str(error)
            )

            audit_event(
                "dataset_validation_failed",
                status="failed",
                details={
                    "filename": filename,
                    "target": target_column,
                    "error": str(error),
                    "error_code": error.code,
                    "details": error.details,
                },
            )

            log_error(
                f"Dataset validation failed: {error}"
            )

            st.error(
                f"❌ Dataset validation failed: {error}"
            )

            if error.details:

                with st.expander(
                    "🔎 Validation Details"
                ):

                    st.json(
                        json_safe(
                            error.details
                        )
                    )

        # =====================================================
        # GENERAL ANALYSIS ERROR
        # =====================================================

        except Exception as error:

            progress.empty()
            status_box.empty()

            st.session_state.analysis_completed = (
                False
            )

            st.session_state.last_error = (
                str(error)
            )

            audit_event(
                "analysis_failed",
                status="failed",
                details={
                    "filename": filename,
                    "target": target_column,
                    "error": str(error),
                },
            )

            log_exception(
                f"NEXUS analysis failed: {error}"
            )

            st.error(
                f"❌ NEXUS analysis failed: {error}"
            )


# ============================================================
# RESULTS
# ============================================================

results = st.session_state.get(
    "analysis_results"
)

dataframe = st.session_state.get(
    "analysis_dataframe"
)


if (
    isinstance(
        results,
        dict,
    )
    and isinstance(
        dataframe,
        pd.DataFrame,
    )
):

    st.divider()

    st.header(
        "📈 NEXUS AI Intelligence Results"
    )

    # ========================================================
    # EXECUTIVE SUMMARY
    # ========================================================

    st.subheader(
        "🎯 Executive Summary"
    )

    summary = results.get(
        "summary"
    )

    if summary is None:

        summary = results.get(
            "executive_summary"
        )

    if summary is None:

        summary = results.get(
            "overview"
        )

    if isinstance(
        summary,
        dict,
    ):

        summary_rows = []

        for key, value in summary.items():

            if isinstance(
                value,
                (
                    dict,
                    list,
                    tuple,
                    set,
                ),
            ):

                value = safe_json_string(
                    value
                )

            summary_rows.append(
                {
                    "Metric": safe_string(
                        key
                    ),
                    "Value": safe_string(
                        value
                    ),
                }
            )

        if summary_rows:

            display_dataframe(
                pd.DataFrame(
                    summary_rows
                )
            )

    elif summary:

        st.write(
            summary
        )

    else:

        st.info(
            "No executive summary was returned."
        )

    # ========================================================
    # KEY METRICS
    # ========================================================

    st.subheader(
        "📊 Key Metrics"
    )

    numeric_columns = list(
        dataframe.select_dtypes(
            include="number"
        ).columns
    )

    if numeric_columns:

        metric_columns = st.columns(
            min(
                len(numeric_columns),
                4,
            )
        )

        for index, column in enumerate(
            numeric_columns[:4]
        ):

            series = pd.to_numeric(
                dataframe[column],
                errors="coerce",
            ).dropna()

            if series.empty:
                continue

            metric_columns[
                index
            ].metric(
                safe_string(
                    column
                ),
                f"{series.sum():,.2f}",
                help="Column total",
            )

    else:

        st.info(
            "No numeric metrics available."
        )

    # ========================================================
    # BUSINESS INSIGHTS
    # ========================================================

    st.divider()

    st.subheader(
        "💡 Business Insights"
    )

    try:

        InsightPanel.render(
            results
        )

    except TypeError:

        try:

            InsightPanel.render(
                results,
                dataframe,
            )

        except Exception as error:

            log_exception(
                f"Insight panel failed: {error}"
            )

            st.warning(
                "Business Insight panel could not be rendered."
            )

    except Exception as error:

        log_exception(
            f"Insight panel failed: {error}"
        )

        st.warning(
            "Business Insight panel could not be rendered."
        )

    # ========================================================
    # ADVANCED INTELLIGENCE
    # ========================================================

    st.divider()

    st.subheader(
        "🧠 Advanced Intelligence"
    )

    try:

        AdvancedPanels.render(
            results,
            dataframe,
        )

    except Exception as error:

        log_exception(
            f"Advanced Panels failed: {error}"
        )

        st.error(
            "Advanced intelligence panels could not be rendered."
        )

    # ========================================================
    # RAW RESULTS
    # ========================================================

    st.divider()

    with st.expander(
        "🔎 Raw NEXUS Results",
        expanded=False,
    ):

        try:

            st.json(
                json_safe(
                    results
                )
            )

        except Exception as error:

            st.code(
                safe_json_string(
                    results
                ),
                language="json",
            )

            log_exception(
                f"Raw result rendering failed: {error}"
            )

    # ========================================================
    # VALIDATION DETAILS
    # ========================================================

    validation_results = results.get(
        "validation"
    )

    if validation_results:

        st.divider()

        with st.expander(
            "✅ Dataset Validation",
            expanded=False,
        ):

            st.json(
                json_safe(
                    validation_results
                )
            )

    # ========================================================
    # ANALYSIS METADATA
    # ========================================================

    st.divider()

    with st.expander(
        "ℹ️ Analysis Metadata",
        expanded=False,
    ):

        metadata = {
            "Application": APP_NAME,
            "Version": APP_VERSION,
            "Dataset": st.session_state.get(
                "uploaded_filename"
            ),
            "Target": st.session_state.get(
                "analysis_target"
            ),
            "Rows": len(
                dataframe
            ),
            "Columns": len(
                dataframe.columns
            ),
            "Analysis Time": st.session_state.get(
                "analysis_timestamp"
            ),
        }

        metadata_df = pd.DataFrame(
            {
                "Property": list(
                    metadata.keys()
                ),
                "Value": [
                    safe_string(
                        value
                    )
                    for value in metadata.values()
                ],
            }
        )

        display_dataframe(
            metadata_df
        )


# ============================================================
# REPORT SECTION
# ============================================================

if (
    isinstance(
        results,
        dict,
    )
    and isinstance(
        dataframe,
        pd.DataFrame,
    )
    and not dataframe.empty
):

    st.divider()

    st.header(
        "📄 Reports"
    )

    st.write(
        "Generate a professional PDF report "
        "from the completed NEXUS analysis."
    )

    if st.button(
        "📄 Generate PDF Report",
        use_container_width=True,
    ):

        try:

            from app.services.report_generator import (
                generate_report,
            )

            audit_event(
                "report_generation_started",
                details={
                    "dataset": st.session_state.get(
                        "uploaded_filename"
                    ),
                },
            )

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

                raise TypeError(
                    "Report generator did not return PDF bytes."
                )

            report_filename = (
                "nexus_ai_report.pdf"
            )

            st.download_button(
                "⬇️ Download PDF Report",
                data=bytes(
                    pdf_bytes
                ),
                file_name=report_filename,
                mime="application/pdf",
                use_container_width=True,
            )

            audit_event(
                "report_generation_completed",
                details={
                    "filename": report_filename,
                    "bytes": len(
                        pdf_bytes
                    ),
                },
            )

            st.success(
                "✅ PDF report generated successfully."
            )

        except ImportError:

            st.error(
                "❌ Report generator is unavailable."
            )

        except Exception as error:

            log_exception(
                f"Report generation failed: {error}"
            )

            audit_event(
                "report_generation_failed",
                status="failed",
                details={
                    "error": str(error),
                },
            )

            st.error(
                f"❌ Report generation failed: {error}"
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    f"{APP_NAME} v{APP_VERSION} • "
    "Autonomous Enterprise Intelligence"
)