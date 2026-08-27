from __future__ import annotations

# ============================================================
# NEXUS AI — ADVANCED PANELS
# ============================================================

import json
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# OPTIONAL ANALYTICS IMPORTS
# ============================================================

try:
    from app.analytics.anomaly import AnomalyDetector
except Exception:
    AnomalyDetector = None


# ============================================================
# ADVANCED PANELS
# ============================================================


class AdvancedPanels:
    """
    Production-safe Streamlit UI for NEXUS AI.

    Main responsibilities:

    - Render intelligence returned by the orchestrator
    - Safely display DataFrames
    - Prevent pandas truth-value errors
    - Prevent PyArrow serialization errors
    - Render nested dictionaries/lists safely
    - Display KPIs
    - Display statistics
    - Display correlations
    - Display anomalies
    - Display distributions
    - Display drivers
    - Display target intelligence
    - Display ML readiness
    - Display decision intelligence
    - Display recommendations
    """

    # ========================================================
    # SAFE HELPERS
    # ========================================================

    @staticmethod
    def _safe_get(
        results: dict[str, Any] | None,
        key: str,
        default: Any = None,
    ) -> Any:

        if not isinstance(results, dict):
            return default

        return results.get(
            key,
            default,
        )

    # ========================================================

    @staticmethod
    def _is_empty(
        value: Any,
    ) -> bool:

        if value is None:
            return True

        if isinstance(
            value,
            pd.DataFrame,
        ):
            return value.empty

        if isinstance(
            value,
            pd.Series,
        ):
            return value.empty

        if isinstance(
            value,
            dict,
        ):
            return len(value) == 0

        if isinstance(
            value,
            (list, tuple, set),
        ):
            return len(value) == 0

        if isinstance(
            value,
            str,
        ):
            return not value.strip()

        return False

    # ========================================================

    @staticmethod
    def _scalar_safe(
        value: Any,
    ) -> Any:
        """
        Convert arbitrary Python objects into Arrow-safe
        DataFrame cell values.
        """

        if value is None:
            return None

        # ----------------------------------------------------
        # DataFrame
        # ----------------------------------------------------

        if isinstance(
            value,
            pd.DataFrame,
        ):

            if value.empty:
                return ""

            try:

                return json.dumps(
                    AdvancedPanels._json_safe(
                        value.to_dict(
                            orient="records"
                        )
                    ),
                    default=str,
                    ensure_ascii=False,
                )

            except Exception:

                return value.to_string(
                    index=False
                )

        # ----------------------------------------------------
        # Series
        # ----------------------------------------------------

        if isinstance(
            value,
            pd.Series,
        ):

            try:

                return json.dumps(
                    AdvancedPanels._json_safe(
                        value.to_dict()
                    ),
                    default=str,
                    ensure_ascii=False,
                )

            except Exception:

                return value.to_string()

        # ----------------------------------------------------
        # Dictionary
        # ----------------------------------------------------

        if isinstance(
            value,
            dict,
        ):

            try:

                return json.dumps(
                    AdvancedPanels._json_safe(
                        value
                    ),
                    default=str,
                    ensure_ascii=False,
                )

            except Exception:

                return str(value)

        # ----------------------------------------------------
        # List / Tuple / Set
        # ----------------------------------------------------

        if isinstance(
            value,
            (list, tuple, set),
        ):

            try:

                return json.dumps(
                    AdvancedPanels._json_safe(
                        list(value)
                    ),
                    default=str,
                    ensure_ascii=False,
                )

            except Exception:

                return str(value)

        # ----------------------------------------------------
        # NumPy values
        # ----------------------------------------------------

        if isinstance(
            value,
            np.ndarray,
        ):

            try:

                return json.dumps(
                    AdvancedPanels._json_safe(
                        value.tolist()
                    ),
                    default=str,
                    ensure_ascii=False,
                )

            except Exception:

                return str(value)

        if isinstance(
            value,
            np.integer,
        ):

            return int(value)

        if isinstance(
            value,
            np.floating,
        ):

            number = float(value)

            if not np.isfinite(number):
                return None

            return number

        if isinstance(
            value,
            np.bool_,
        ):

            return bool(value)

        # ----------------------------------------------------
        # Timestamp
        # ----------------------------------------------------

        if isinstance(
            value,
            pd.Timestamp,
        ):

            return value.isoformat()

        # ----------------------------------------------------
        # Missing values
        # ----------------------------------------------------

        try:

            missing = pd.isna(value)

            if isinstance(
                missing,
                (bool, np.bool_),
            ) and missing:

                return None

        except Exception:
            pass

        # ----------------------------------------------------
        # Primitive values
        # ----------------------------------------------------

        if isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
            ),
        ):

            if isinstance(
                value,
                float,
            ) and not np.isfinite(value):

                return None

            return value

        # ----------------------------------------------------
        # Final fallback
        # ----------------------------------------------------

        return str(value)

    # ========================================================

    @staticmethod
    def _json_safe(
        value: Any,
    ) -> Any:
        """
        Recursively convert NEXUS result objects into
        JSON-compatible Python values.
        """

        if value is None:
            return None

        if isinstance(
            value,
            pd.DataFrame,
        ):

            return [
                {
                    str(key):
                    AdvancedPanels._json_safe(item)
                    for key, item in row.items()
                }
                for row in value.to_dict(
                    orient="records"
                )
            ]

        if isinstance(
            value,
            pd.Series,
        ):

            return {
                str(key):
                AdvancedPanels._json_safe(item)
                for key, item in value.to_dict().items()
            }

        if isinstance(
            value,
            np.ndarray,
        ):

            return AdvancedPanels._json_safe(
                value.tolist()
            )

        if isinstance(
            value,
            np.integer,
        ):

            return int(value)

        if isinstance(
            value,
            np.floating,
        ):

            number = float(value)

            if not np.isfinite(number):
                return None

            return number

        if isinstance(
            value,
            np.bool_,
        ):

            return bool(value)

        if isinstance(
            value,
            dict,
        ):

            return {
                str(key):
                AdvancedPanels._json_safe(item)
                for key, item in value.items()
            }

        if isinstance(
            value,
            (list, tuple, set),
        ):

            return [
                AdvancedPanels._json_safe(item)
                for item in value
            ]

        if isinstance(
            value,
            pd.Timestamp,
        ):

            return value.isoformat()

        try:

            missing = pd.isna(value)

            if isinstance(
                missing,
                (bool, np.bool_),
            ) and missing:

                return None

        except Exception:
            pass

        return value

    # ========================================================

    @staticmethod
    def _format_number(
        value: Any,
        decimals: int = 2,
    ) -> str:

        try:

            if value is None:
                return "—"

            if isinstance(
                value,
                str,
            ):

                return value

            number = float(value)

            if not np.isfinite(number):
                return "—"

            return f"{number:,.{decimals}f}"

        except Exception:

            return str(value)

    # ========================================================

    @staticmethod
    def _format_percent(
        value: Any,
        decimals: int = 2,
    ) -> str:

        try:

            number = float(value)

            if not np.isfinite(number):
                return "—"

            return f"{number:.{decimals}f}%"

        except Exception:

            return str(value)

    # ========================================================
    # ARROW SAFE DATAFRAME
    # ========================================================

    @staticmethod
    def _make_arrow_safe_dataframe(
        dataframe: Any,
    ) -> pd.DataFrame:
        """
        Convert any table-like object into an Arrow-safe
        DataFrame.

        This is the main fix for the PyArrow errors.
        """

        if dataframe is None:
            return pd.DataFrame()

        # ----------------------------------------------------
        # DataFrame
        # ----------------------------------------------------

        if isinstance(
            dataframe,
            pd.DataFrame,
        ):

            safe_df = dataframe.copy()

        # ----------------------------------------------------
        # Series
        # ----------------------------------------------------

        elif isinstance(
            dataframe,
            pd.Series,
        ):

            safe_df = dataframe.to_frame()

        # ----------------------------------------------------
        # Dictionary
        # ----------------------------------------------------

        elif isinstance(
            dataframe,
            dict,
        ):

            try:

                safe_df = pd.DataFrame(
                    dataframe
                )

            except Exception:

                safe_df = pd.DataFrame(
                    {
                        "key": [
                            str(key)
                            for key in dataframe
                        ],
                        "value": [
                            AdvancedPanels._scalar_safe(
                                value
                            )
                            for value in dataframe.values()
                        ],
                    }
                )

        # ----------------------------------------------------
        # List
        # ----------------------------------------------------

        elif isinstance(
            dataframe,
            (list, tuple),
        ):

            try:

                safe_df = pd.DataFrame(
                    dataframe
                )

            except Exception:

                safe_df = pd.DataFrame(
                    {
                        "value": [
                            AdvancedPanels._scalar_safe(
                                value
                            )
                            for value in dataframe
                        ]
                    }
                )

        else:

            safe_df = pd.DataFrame(
                {
                    "value": [
                        AdvancedPanels._scalar_safe(
                            dataframe
                        )
                    ]
                }
            )

        if safe_df.empty:
            return safe_df.reset_index(
                drop=True
            )

        # ----------------------------------------------------
        # Reset index
        # ----------------------------------------------------

        safe_df = safe_df.reset_index(
            drop=True
        )

        # ----------------------------------------------------
        # Safe column names
        # ----------------------------------------------------

        safe_df.columns = [
            str(column)
            for column in safe_df.columns
        ]

        # ----------------------------------------------------
        # Safe every cell
        # ----------------------------------------------------

        for column in safe_df.columns:

            safe_df[column] = (
                safe_df[column]
                .map(
                    AdvancedPanels._scalar_safe
                )
            )

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Object columns may contain:
        #
        # int
        # float
        # dict
        # DataFrame
        # string
        #
        # Arrow cannot safely serialize such mixed columns.
        #
        # Convert object columns to strings.
        # ----------------------------------------------------

        for column in safe_df.columns:

            if (
                safe_df[column].dtype
                == "object"
            ):

                safe_df[column] = (
                    safe_df[column]
                    .map(
                        lambda value:
                        ""
                        if value is None
                        else str(value)
                    )
                )

        return safe_df

    # ========================================================
    # DISPLAY DATAFRAME
    # ========================================================

    @staticmethod
    def _display_dataframe(
        dataframe: Any,
        height: int | None = None,
    ) -> None:

        safe_df = (
            AdvancedPanels
            ._make_arrow_safe_dataframe(
                dataframe
            )
        )

        if safe_df.empty:

            st.info(
                "No tabular data available."
            )

            return

        kwargs = {
            "width": "stretch",
            "hide_index": True,
        }

        if height is not None:
            kwargs["height"] = height

        try:

            st.dataframe(
                safe_df,
                **kwargs,
            )

        except Exception:

            try:

                fallback = safe_df.astype(
                    str
                )

                st.dataframe(
                    fallback,
                    **kwargs,
                )

            except Exception:

                st.code(
                    safe_df.to_string(
                        index=False
                    )
                )

    # ========================================================
    # DISPLAY JSON
    # ========================================================

    @staticmethod
    def _display_json(
        value: Any,
    ) -> None:

        try:

            safe = (
                AdvancedPanels
                ._json_safe(value)
            )

            st.json(
                safe
            )

        except Exception:

            st.code(
                str(value)
            )

    # ========================================================
    # FIND DATAFRAME
    # ========================================================

    @staticmethod
    def _find_dataframe(
        value: Any,
    ) -> pd.DataFrame | None:

        if isinstance(
            value,
            pd.DataFrame,
        ):

            return value

        if isinstance(
            value,
            dict,
        ):

            for item in value.values():

                found = (
                    AdvancedPanels
                    ._find_dataframe(item)
                )

                if found is not None:
                    return found

        if isinstance(
            value,
            (list, tuple),
        ):

            for item in value:

                found = (
                    AdvancedPanels
                    ._find_dataframe(item)
                )

                if found is not None:
                    return found

        return None

    # ========================================================
    # SECTION HEADER
    # ========================================================

    @staticmethod
    def _section(
        title: str,
        description: str | None = None,
    ) -> None:

        st.markdown(
            f"## {title}"
        )

        if description:

            st.caption(
                description
            )

    # ========================================================
    # OVERVIEW
    # ========================================================

    @staticmethod
    def overview(
        results: dict[str, Any],
        dataframe: pd.DataFrame,
    ) -> None:

        AdvancedPanels._section(
            "📊 Intelligence Overview",
            "High-level enterprise intelligence generated by NEXUS AI.",
        )

        rows = len(dataframe)

        columns = len(
            dataframe.columns
        )

        missing = int(
            dataframe.isna()
            .sum()
            .sum()
        )

        duplicates = int(
            dataframe
            .duplicated()
            .sum()
        )

        numeric = len(
            dataframe
            .select_dtypes(
                include="number"
            )
            .columns
        )

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "Rows",
            f"{rows:,}",
        )

        c2.metric(
            "Columns",
            f"{columns:,}",
        )

        c3.metric(
            "Numeric Fields",
            f"{numeric:,}",
        )

        c4.metric(
            "Missing Values",
            f"{missing:,}",
        )

        c5.metric(
            "Duplicates",
            f"{duplicates:,}",
        )

    # ========================================================
    # STATISTICS
    # ========================================================

    @staticmethod
    def statistics(
        results: dict[str, Any],
    ) -> None:

        value = (
            results.get(
                "statistics"
            )
        )

        if AdvancedPanels._is_empty(
            value
        ):

            return

        with st.expander(
            "📐 Statistical Intelligence",
            expanded=False,
        ):

            if isinstance(
                value,
                pd.DataFrame,
            ):

                AdvancedPanels._display_dataframe(
                    value
                )

            else:

                dataframe = (
                    AdvancedPanels
                    ._find_dataframe(value)
                )

                if dataframe is not None:

                    AdvancedPanels._display_dataframe(
                        dataframe
                    )

                else:

                    AdvancedPanels._display_json(
                        value
                    )

    # ========================================================
    # CORRELATIONS
    # ========================================================

    @staticmethod
    def correlations(
        results: dict[str, Any],
    ) -> None:

        value = (
            results.get(
                "correlations"
            )
        )

        if AdvancedPanels._is_empty(
            value
        ):

            return

        with st.expander(
            "🔗 Correlation Intelligence",
            expanded=False,
        ):

            dataframe = (
                AdvancedPanels
                ._find_dataframe(value)
            )

            if dataframe is not None:

                AdvancedPanels._display_dataframe(
                    dataframe
                )

                # --------------------------------------------
                # Heatmap when numeric
                # --------------------------------------------

                numeric = (
                    dataframe
                    .select_dtypes(
                        include="number"
                    )
                )

                if (
                    not numeric.empty
                    and len(numeric.columns) >= 2
                ):

                    try:

                        correlation_matrix = (
                            numeric.corr()
                        )

                        figure = px.imshow(
                            correlation_matrix,
                            text_auto=True,
                            title="Correlation Matrix",
                        )

                        st.plotly_chart(
                            figure,
                            width="stretch",
                        )

                    except Exception:
                        pass

            else:

                AdvancedPanels._display_json(
                    value
                )

    # ========================================================
    # ANOMALIES
    # ========================================================

    @staticmethod
    def anomalies(
        results: dict[str, Any],
        dataframe: pd.DataFrame,
    ) -> None:

        value = (
            results.get(
                "anomalies"
            )
        )

        if AdvancedPanels._is_empty(
            value
        ):

            return

        with st.expander(
            "🚨 Anomaly Intelligence",
            expanded=False,
        ):

            if isinstance(
                value,
                pd.DataFrame,
            ):

                AdvancedPanels._display_dataframe(
                    value
                )

                return

            if isinstance(
                value,
                dict,
            ):

                # --------------------------------------------
                # Common anomaly structure
                # --------------------------------------------

                summary = []

                for key, item in value.items():

                    if isinstance(
                        item,
                        dict,
                    ):

                        row = {
                            "Metric": key,
                            **{
                                str(k):
                                AdvancedPanels._scalar_safe(v)
                                for k, v in item.items()
                            },
                        }

                        summary.append(
                            row
                        )

                    else:

                        summary.append(
                            {
                                "Metric": key,
                                "Value":
                                AdvancedPanels._scalar_safe(
                                    item
                                ),
                            }
                        )

                if summary:

                    AdvancedPanels._display_dataframe(
                        pd.DataFrame(
                            summary
                        )
                    )

                else:

                    AdvancedPanels._display_json(
                        value
                    )

                return

            AdvancedPanels._display_json(
                value
            )

    # ========================================================
    # DISTRIBUTIONS
    # ========================================================

    @staticmethod
    def distributions(
        results: dict[str, Any],
        dataframe: pd.DataFrame,
    ) -> None:

        value = (
            results.get(
                "distributions"
            )
        )

        with st.expander(
            "📈 Distribution Intelligence",
            expanded=False,
        ):

            if (
                isinstance(
                    value,
                    dict,
                )
                and value
            ):

                AdvancedPanels._display_json(
                    value
                )

            else:

                numeric_columns = (
                    dataframe
                    .select_dtypes(
                        include="number"
                    )
                    .columns
                    .tolist()
                )

                if not numeric_columns:

                    st.info(
                        "No numeric columns available."
                    )

                    return

                selected = st.selectbox(
                    "Select metric",
                    numeric_columns,
                    key="distribution_metric",
                )

                series = pd.to_numeric(
                    dataframe[selected],
                    errors="coerce",
                ).dropna()

                if series.empty:

                    st.info(
                        "No usable values."
                    )

                    return

                figure = px.histogram(
                    series,
                    x=selected,
                    nbins=30,
                    title=f"Distribution of {selected}",
                )

                st.plotly_chart(
                    figure,
                    width="stretch",
                )

    # ========================================================
    # DRIVERS
    # ========================================================

    @staticmethod
    def drivers(
        results: dict[str, Any],
    ) -> None:

        value = (
            results.get(
                "drivers"
            )
        )

        if AdvancedPanels._is_empty(
            value
        ):

            return

        with st.expander(
            "🎯 Business Drivers",
            expanded=False,
        ):

            dataframe = (
                AdvancedPanels
                ._find_dataframe(value)
            )

            if dataframe is not None:

                AdvancedPanels._display_dataframe(
                    dataframe
                )

            else:

                AdvancedPanels._display_json(
                    value
                )

    # ========================================================
    # KPI INTELLIGENCE
    # ========================================================

    @staticmethod
    def kpis(
        results: dict[str, Any],
        dataframe: pd.DataFrame,
    ) -> None:

        value = (
            results.get(
                "kpis"
            )
        )

        AdvancedPanels._section(
            "📌 KPI Intelligence",
            "Automatically detected business performance indicators.",
        )

        if not AdvancedPanels._is_empty(
            value
        ):

            dataframe_result = (
                AdvancedPanels
                ._find_dataframe(value)
            )

            if dataframe_result is not None:

                AdvancedPanels._display_dataframe(
                    dataframe_result
                )

            elif isinstance(
                value,
                dict,
            ):

                cards = []

                for key, item in value.items():

                    if isinstance(
                        item,
                        dict,
                    ):

                        cards.append(
                            (
                                str(key),
                                item.get(
                                    "value",
                                    item.get(
                                        "current",
                                        item.get(
                                            "score",
                                            "—"
                                        )
                                    ),
                                ),
                            )
                        )

                    else:

                        cards.append(
                            (
                                str(key),
                                item,
                            )
                        )

                if cards:

                    columns = st.columns(
                        min(
                            len(cards),
                            4
                        )
                    )

                    for index, (
                        label,
                        metric_value,
                    ) in enumerate(cards):

                        columns[
                            index % len(columns)
                        ].metric(
                            label,
                            AdvancedPanels._format_number(
                                metric_value
                            ),
                        )

                else:

                    AdvancedPanels._display_json(
                        value
                    )

            else:

                AdvancedPanels._display_json(
                    value
                )

        else:

            numeric = (
                dataframe
                .select_dtypes(
                    include="number"
                )
            )

            if numeric.empty:

                st.info(
                    "No numeric business metrics detected."
                )

                return

            cards = numeric.sum()

            columns = st.columns(
                min(
                    len(cards),
                    4
                )
            )

            for index, (
                column,
                value_sum,
            ) in enumerate(
                cards.items()
            ):

                columns[
                    index % len(columns)
                ].metric(
                    str(column),
                    AdvancedPanels._format_number(
                        value_sum
                    ),
                )

    # ========================================================
    # TARGET INTELLIGENCE
    # ========================================================

    @staticmethod
    def target_intelligence(
        results: dict[str, Any],
        dataframe: pd.DataFrame,
    ) -> None:

        value = (
            results.get(
                "target_analysis"
            )
            or results.get(
                "target_intelligence"
            )
        )

        if AdvancedPanels._is_empty(
            value
        ):

            return

        with st.expander(
            "🎯 Target Intelligence",
            expanded=False,
        ):

            dataframe_result = (
                AdvancedPanels
                ._find_dataframe(value)
            )

            if dataframe_result is not None:

                AdvancedPanels._display_dataframe(
                    dataframe_result
                )

            else:

                AdvancedPanels._display_json(
                    value
                )

    # ========================================================
    # ML READINESS
    # ========================================================

    @staticmethod
    def ml_readiness(
        results: dict[str, Any],
    ) -> None:

        value = (
            results.get(
                "ml_readiness"
            )
        )

        if AdvancedPanels._is_empty(
            value
        ):

            return

        with st.expander(
            "🤖 ML Readiness",
            expanded=False,
        ):

            if isinstance(
                value,
                dict,
            ):

                score = (
                    value.get(
                        "score"
                    )
                    or value.get(
                        "readiness_score"
                    )
                )

                if score is not None:

                    try:

                        score_number = float(
                            score
                        )

                        st.metric(
                            "ML Readiness Score",
                            f"{score_number:.1f}",
                        )

                        st.progress(
                            max(
                                0.0,
                                min(
                                    score_number / 100,
                                    1.0,
                                ),
                            )
                        )

                    except Exception:
                        pass

            AdvancedPanels._display_json(
                value
            )

    # ========================================================
    # RISK INTELLIGENCE
    # ========================================================

    @staticmethod
    def risk_intelligence(
        results: dict[str, Any],
    ) -> None:

        value = (
            results.get(
                "risk"
            )
            or results.get(
                "risk_intelligence"
            )
        )

        if AdvancedPanels._is_empty(
            value
        ):

            return

        with st.expander(
            "⚠️ Risk Intelligence",
            expanded=False,
        ):

            if isinstance(
                value,
                dict,
            ):

                risk_level = (
                    value.get(
                        "risk_level"
                    )
                    or value.get(
                        "level"
                    )
                )

                if risk_level:

                    st.metric(
                        "Risk Level",
                        str(
                            risk_level
                        ).upper(),
                    )

            AdvancedPanels._display_json(
                value
            )

    # ========================================================
    # RECOMMENDATIONS
    # ========================================================

    @staticmethod
    def recommendations(
        results: dict[str, Any],
    ) -> None:

        value = (
            results.get(
                "recommendations"
            )
        )

        if AdvancedPanels._is_empty(
            value
        ):

            return

        AdvancedPanels._section(
            "💡 Executive Recommendations",
            "Actions suggested by NEXUS AI from the analyzed business evidence.",
        )

        if isinstance(
            value,
            list,
        ):

            for index, item in enumerate(
                value,
                start=1,
            ):

                if isinstance(
                    item,
                    dict,
                ):

                    title = (
                        item.get(
                            "title"
                        )
                        or item.get(
                            "recommendation"
                        )
                        or f"Recommendation {index}"
                    )

                    st.markdown(
                        f"### {index}. {title}"
                    )

                    description = (
                        item.get(
                            "description"
                        )
                        or item.get(
                            "reason"
                        )
                        or item.get(
                            "action"
                        )
                    )

                    if description:

                        st.write(
                            str(
                                description
                            )
                        )

                else:

                    st.markdown(
                        f"### {index}. {item}"
                    )

        elif isinstance(
            value,
            str,
        ):

            st.write(
                value
            )

        else:

            AdvancedPanels._display_json(
                value
            )

    # ========================================================
    # EXECUTIVE SUMMARY
    # ========================================================

    @staticmethod
    def executive_summary(
        results: dict[str, Any],
    ) -> None:

        value = (
            results.get(
                "executive_summary"
            )
            or results.get(
                "summary"
            )
        )

        if AdvancedPanels._is_empty(
            value
        ):

            return

        AdvancedPanels._section(
            "🧑‍💼 Executive Summary",
            "Management-level interpretation of the NEXUS intelligence output.",
        )

        if isinstance(
            value,
            str,
        ):

            st.info(
                value
            )

        elif isinstance(
            value,
            dict,
        ):

            summary = (
                value.get(
                    "summary"
                )
                or value.get(
                    "text"
                )
                or value.get(
                    "message"
                )
            )

            if summary:

                st.info(
                    str(summary)
                )

            AdvancedPanels._display_json(
                value
            )

        else:

            AdvancedPanels._display_json(
                value
            )

    # ========================================================
    # DECISION INTELLIGENCE
    # ========================================================

    @staticmethod
    def decision_intelligence(
        results: dict[str, Any],
        dataframe: pd.DataFrame | None = None,
    ) -> None:

        st.markdown(
            "## 🧠 Decision Intelligence"
        )

        st.caption(
            "Test business decisions through NEXUS AI what-if simulation."
        )

        if (
            dataframe is None
            or dataframe.empty
        ):

            st.info(
                "Upload a dataset to activate decision intelligence."
            )

            return

        numeric_columns = (
            dataframe
            .select_dtypes(
                include="number"
            )
            .columns
            .tolist()
        )

        if not numeric_columns:

            st.warning(
                "No numerical business metrics were detected."
            )

            return

        # ----------------------------------------------------
        # Revenue candidates
        # ----------------------------------------------------

        revenue_candidates = [
            column
            for column in numeric_columns
            if any(
                word in column.lower()
                for word in [
                    "revenue",
                    "sales",
                    "income",
                    "turnover",
                ]
            )
        ]

        # ----------------------------------------------------
        # Profit candidates
        # ----------------------------------------------------

        profit_candidates = [
            column
            for column in numeric_columns
            if any(
                word in column.lower()
                for word in [
                    "profit",
                    "earnings",
                    "net_income",
                    "net profit",
                ]
            )
        ]

        c1, c2 = st.columns(2)

        with c1:

            revenue_column = st.selectbox(
                "Revenue / Sales Metric",
                revenue_candidates
                if revenue_candidates
                else numeric_columns,
                key="decision_revenue_column",
            )

        with c2:

            profit_column = st.selectbox(
                "Profit Metric",
                profit_candidates
                if profit_candidates
                else numeric_columns,
                key="decision_profit_column",
            )

        # ----------------------------------------------------
        # Convert safely
        # ----------------------------------------------------

        revenue = pd.to_numeric(
            dataframe[
                revenue_column
            ],
            errors="coerce",
        ).fillna(
            0
        ).sum()

        profit = pd.to_numeric(
            dataframe[
                profit_column
            ],
            errors="coerce",
        ).fillna(
            0
        ).sum()

        revenue = float(
            revenue
        )

        profit = float(
            profit
        )

        margin = (
            profit
            / revenue
            * 100
            if revenue
            else 0
        )

        st.divider()

        m1, m2, m3 = st.columns(3)

        m1.metric(
            "Current Revenue",
            f"₹{revenue:,.2f}",
        )

        m2.metric(
            "Current Profit",
            f"₹{profit:,.2f}",
        )

        m3.metric(
            "Profit Margin",
            f"{margin:.2f}%",
        )

        # ----------------------------------------------------
        # Simulator
        # ----------------------------------------------------

        st.markdown(
            "### 🎛️ What-If Business Simulator"
        )

        st.caption(
            "Change strategic assumptions and estimate their impact."
        )

        s1, s2 = st.columns(2)

        with s1:

            price = st.slider(
                "Price Change (%)",
                -50.0,
                50.0,
                0.0,
                1.0,
                key="scenario_price",
            )

            demand = st.slider(
                "Demand Change (%)",
                -80.0,
                100.0,
                0.0,
                1.0,
                key="scenario_demand",
            )

            marketing = st.slider(
                "Marketing Change (%)",
                -100.0,
                300.0,
                0.0,
                5.0,
                key="scenario_marketing",
            )

        with s2:

            variable_cost = st.slider(
                "Variable Cost Change (%)",
                -50.0,
                100.0,
                0.0,
                1.0,
                key="scenario_variable_cost",
            )

            fixed_cost = st.slider(
                "Fixed Cost Change (%)",
                -50.0,
                100.0,
                0.0,
                1.0,
                key="scenario_fixed_cost",
            )

        # ----------------------------------------------------
        # Decision engine
        # ----------------------------------------------------

        try:

            from app.analytics.decision_engine import (
                DecisionEngine,
                Scenario,
            )

        except ImportError:

            st.error(
                "Decision engine module is not available. "
                "Check app/analytics/decision_engine.py."
            )

            return

        try:

            scenario = Scenario(
                name="Custom Scenario",
                price_change_pct=price,
                demand_change_pct=demand,
                marketing_change_pct=marketing,
                variable_cost_change_pct=variable_cost,
                fixed_cost_change_pct=fixed_cost,
            )

            simulation = (
                DecisionEngine.simulate(
                    revenue=revenue,
                    profit=profit,
                    scenario=scenario,
                )
            )

            if not isinstance(
                simulation,
                dict,
            ):

                raise TypeError(
                    "Decision engine returned an invalid result."
                )

            # ------------------------------------------------
            # Values
            # ------------------------------------------------

            new_revenue = float(
                simulation.get(
                    "revenue",
                    revenue,
                )
                or 0
            )

            new_profit = float(
                simulation.get(
                    "profit",
                    profit,
                )
                or 0
            )

            revenue_change = float(
                simulation.get(
                    "revenue_change_pct",
                    0,
                )
                or 0
            )

            profit_change = float(
                simulation.get(
                    "profit_change_pct",
                    0,
                )
                or 0
            )

            projected_margin = (
                new_profit
                / new_revenue
                * 100
                if new_revenue
                else 0
            )

            # ------------------------------------------------
            # Result cards
            # ------------------------------------------------

            st.divider()

            st.markdown(
                "### 📊 Simulation Result"
            )

            r1, r2, r3, r4 = st.columns(4)

            r1.metric(
                "Projected Revenue",
                f"₹{new_revenue:,.2f}",
                f"{revenue_change:+.2f}%",
            )

            r2.metric(
                "Projected Profit",
                f"₹{new_profit:,.2f}",
                f"{profit_change:+.2f}%",
            )

            r3.metric(
                "Projected Margin",
                f"{projected_margin:.2f}%",
            )

            r4.metric(
                "Profit Delta",
                f"₹{new_profit - profit:,.2f}",
            )

            # ------------------------------------------------
            # Recommendation
            # ------------------------------------------------

            if new_profit > profit:

                st.success(
                    "🟢 NEXUS recommends this scenario. "
                    "Projected profit increases."
                )

            elif new_profit < profit:

                st.error(
                    "🔴 NEXUS flags this scenario. "
                    "Projected profit decreases."
                )

            else:

                st.info(
                    "🟡 This scenario produces approximately "
                    "the same projected profit."
                )

            # ------------------------------------------------
            # Comparison table
            # ------------------------------------------------

            comparison = pd.DataFrame(
                {
                    "Metric": [
                        "Revenue",
                        "Profit",
                        "Margin",
                    ],
                    "Current": [
                        revenue,
                        profit,
                        margin,
                    ],
                    "Projected": [
                        new_revenue,
                        new_profit,
                        projected_margin,
                    ],
                    "Change %": [
                        revenue_change,
                        profit_change,
                        projected_margin - margin,
                    ],
                }
            )

            AdvancedPanels._display_dataframe(
                comparison
            )

            # ------------------------------------------------
            # Visualization
            # ------------------------------------------------

            chart_data = pd.DataFrame(
                {
                    "Metric": [
                        "Revenue",
                        "Profit",
                    ],
                    "Current": [
                        revenue,
                        profit,
                    ],
                    "Projected": [
                        new_revenue,
                        new_profit,
                    ],
                }
            )

            chart_long = chart_data.melt(
                id_vars="Metric",
                var_name="Scenario",
                value_name="Value",
            )

            figure = px.bar(
                chart_long,
                x="Metric",
                y="Value",
                color="Scenario",
                barmode="group",
                title="Current vs Projected Business Outcome",
            )

            st.plotly_chart(
                figure,
                width="stretch",
            )

            # ------------------------------------------------
            # Engine result
            # ------------------------------------------------

            engine_result = results.get(
                "decision_intelligence"
            )

            if not AdvancedPanels._is_empty(
                engine_result
            ):

                with st.expander(
                    "🔬 Engine Decision Intelligence",
                    expanded=False,
                ):

                    dataframe_result = (
                        AdvancedPanels
                        ._find_dataframe(
                            engine_result
                        )
                    )

                    if dataframe_result is not None:

                        AdvancedPanels._display_dataframe(
                            dataframe_result
                        )

                    else:

                        AdvancedPanels._display_json(
                            engine_result
                        )

        except Exception as error:

            st.error(
                f"Decision engine failed: {error}"
            )

    # ========================================================
    # DATA QUALITY
    # ========================================================

    @staticmethod
    def data_quality(
        results: dict[str, Any],
        dataframe: pd.DataFrame,
    ) -> None:

        value = (
            results.get(
                "data_quality"
            )
            or results.get(
                "quality"
            )
        )

        AdvancedPanels._section(
            "🧹 Data Quality",
            "Checks for missing values, duplicates, invalid values and structural issues.",
        )

        missing = int(
            dataframe.isna()
            .sum()
            .sum()
        )

        duplicate_count = int(
            dataframe
            .duplicated()
            .sum()
        )

        total_cells = (
            dataframe.shape[0]
            * dataframe.shape[1]
        )

        missing_pct = (
            missing
            / total_cells
            * 100
            if total_cells
            else 0
        )

        q1, q2, q3 = st.columns(3)

        q1.metric(
            "Missing Cells",
            f"{missing:,}",
        )

        q2.metric(
            "Missing %",
            f"{missing_pct:.2f}%",
        )

        q3.metric(
            "Duplicate Rows",
            f"{duplicate_count:,}",
        )

        if missing == 0 and duplicate_count == 0:

            st.success(
                "🟢 Dataset quality looks clean."
            )

        elif missing_pct < 5:

            st.warning(
                "🟡 Dataset contains minor quality issues."
            )

        else:

            st.error(
                "🔴 Dataset contains significant quality issues."
            )

        if not AdvancedPanels._is_empty(
            value
        ):

            with st.expander(
                "Detailed Data Quality Results"
            ):

                dataframe_result = (
                    AdvancedPanels
                    ._find_dataframe(value)
                )

                if dataframe_result is not None:

                    AdvancedPanels._display_dataframe(
                        dataframe_result
                    )

                else:

                    AdvancedPanels._display_json(
                        value
                    )

    # ========================================================
    # SCHEMA INTELLIGENCE
    # ========================================================

    @staticmethod
    def schema_intelligence(
        results: dict[str, Any],
        dataframe: pd.DataFrame,
    ) -> None:

        value = (
            results.get(
                "schema"
            )
            or results.get(
                "schema_intelligence"
            )
        )

        AdvancedPanels._section(
            "🧬 Schema Intelligence",
            "Understanding the structure and semantic types of your dataset.",
        )

        schema_df = pd.DataFrame(
            {
                "Column": [
                    str(column)
                    for column in dataframe.columns
                ],
                "Data Type": [
                    str(dtype)
                    for dtype in dataframe.dtypes
                ],
                "Non-Null": [
                    int(
                        dataframe[column]
                        .notna()
                        .sum()
                    )
                    for column in dataframe.columns
                ],
                "Missing": [
                    int(
                        dataframe[column]
                        .isna()
                        .sum()
                    )
                    for column in dataframe.columns
                ],
                "Unique": [
                    int(
                        dataframe[column]
                        .nunique(
                            dropna=True
                        )
                    )
                    for column in dataframe.columns
                ],
            }
        )

        AdvancedPanels._display_dataframe(
            schema_df
        )

        if not AdvancedPanels._is_empty(
            value
        ):

            with st.expander(
                "Detailed Schema Intelligence"
            ):

                AdvancedPanels._display_json(
                    value
                )

    # ========================================================
    # RENDER
    # ========================================================

    @staticmethod
    def render(
        results: dict[str, Any],
        dataframe: pd.DataFrame,
    ) -> None:

        if not isinstance(
            results,
            dict,
        ):

            results = {}

        if not isinstance(
            dataframe,
            pd.DataFrame,
        ):

            dataframe = pd.DataFrame(
                dataframe
            )

        # ----------------------------------------------------
        # Main title
        # ----------------------------------------------------

        st.header(
            "🚀 NEXUS AI Advanced Intelligence"
        )

        # ----------------------------------------------------
        # Overview
        # ----------------------------------------------------

        AdvancedPanels.overview(
            results,
            dataframe,
        )

        st.divider()

        # ----------------------------------------------------
        # Quality
        # ----------------------------------------------------

        AdvancedPanels.data_quality(
            results,
            dataframe,
        )

        st.divider()

        # ----------------------------------------------------
        # Schema
        # ----------------------------------------------------

        AdvancedPanels.schema_intelligence(
            results,
            dataframe,
        )

        st.divider()

        # ----------------------------------------------------
        # KPI
        # ----------------------------------------------------

        AdvancedPanels.kpis(
            results,
            dataframe,
        )

        st.divider()

        # ----------------------------------------------------
        # Analytics
        # ----------------------------------------------------

        AdvancedPanels.statistics(
            results
        )

        AdvancedPanels.correlations(
            results
        )

        AdvancedPanels.anomalies(
            results,
            dataframe,
        )

        AdvancedPanels.distributions(
            results,
            dataframe,
        )

        AdvancedPanels.drivers(
            results
        )

        AdvancedPanels.target_intelligence(
            results,
            dataframe,
        )

        # ----------------------------------------------------
        # Intelligence
        # ----------------------------------------------------

        AdvancedPanels.ml_readiness(
            results
        )

        AdvancedPanels.risk_intelligence(
            results
        )

        st.divider()

        # ----------------------------------------------------
        # Decision intelligence
        # ----------------------------------------------------

        AdvancedPanels.decision_intelligence(
            results,
            dataframe,
        )

        st.divider()

        # ----------------------------------------------------
        # Executive intelligence
        # ----------------------------------------------------

        AdvancedPanels.executive_summary(
            results
        )

        AdvancedPanels.recommendations(
            results
        )

    # ========================================================
    # CONVENIENCE METHOD
    # ========================================================

    @staticmethod
    def show(
        results: dict[str, Any],
        dataframe: pd.DataFrame,
    ) -> None:

        AdvancedPanels.render(
            results,
            dataframe,
        )


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================

def render_advanced_panels(
    results: dict[str, Any],
    dataframe: pd.DataFrame,
) -> None:

    AdvancedPanels.render(
        results,
        dataframe,
    )