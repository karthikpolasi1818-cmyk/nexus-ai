from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.analytics.anomaly import AnomalyDetector


# ============================================================
# NEXUS AI — ADVANCED PANELS
# ============================================================


class AdvancedPanels:
    """
    Advanced Streamlit UI layer for NEXUS AI.

    This module is intentionally defensive:
    - Handles DataFrames safely
    - Handles dictionaries/lists safely
    - Avoids pandas truth-value errors
    - Works with missing optional result sections
    - Uses current Streamlit width API
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

        return results.get(key, default)

    @staticmethod
    def _is_empty(value: Any) -> bool:

        if value is None:
            return True

        if isinstance(value, pd.DataFrame):
            return value.empty

        if isinstance(value, pd.Series):
            return value.empty

        if isinstance(value, dict):
            return len(value) == 0

        if isinstance(value, (list, tuple, set)):
            return len(value) == 0

        if isinstance(value, str):
            return not value.strip()

        return False

    @staticmethod
    def _format_number(
        value: Any,
        decimals: int = 2,
    ) -> str:

        try:

            if pd.isna(value):
                return "N/A"

            value = float(value)

            if abs(value) >= 1_000_000_000:
                return f"{value / 1_0**9:.{decimals}f}B"

            if abs(value) >= 1_000_000:
                return f"{value / 1_000_000:.{decimals}f}M"

            if abs(value) >= 1_000:
                return f"{value / 1_000:.{decimals}f}K"

            return f"{value:,.{decimals}f}"

        except Exception:
            return str(value)

    @staticmethod
    def _currency(value: Any) -> str:

        try:
            return f"₹{float(value):,.2f}"
        except Exception:
            return str(value)

    @staticmethod
    def _find_columns(
        dataframe: pd.DataFrame,
        keywords: list[str],
    ) -> list[str]:

        result = []

        for column in dataframe.columns:

            name = str(column).lower()

            if any(
                keyword.lower() in name
                for keyword in keywords
            ):
                result.append(column)

        return result

    @staticmethod
    def _to_dataframe(
        value: Any,
    ) -> pd.DataFrame:

        if value is None:
            return pd.DataFrame()

        if isinstance(value, pd.DataFrame):
            return value.copy()

        if isinstance(value, pd.Series):
            return value.to_frame()

        if isinstance(value, dict):

            if not value:
                return pd.DataFrame()

            try:

                frame = pd.DataFrame(value)

                if not frame.empty:
                    return frame

            except Exception:
                pass

            return pd.DataFrame(
                {
                    "Metric": list(value.keys()),
                    "Value": list(value.values()),
                }
            )

        if isinstance(value, list):

            if not value:
                return pd.DataFrame()

            try:
                return pd.DataFrame(value)
            except Exception:
                return pd.DataFrame(
                    {"Value": value}
                )

        return pd.DataFrame()

    @staticmethod
    def _json_safe(value: Any) -> Any:

        if isinstance(value, pd.DataFrame):
            return value.to_dict(
                orient="records"
            )

        if isinstance(value, pd.Series):
            return value.to_dict()

        if isinstance(value, np.integer):
            return int(value)

        if isinstance(value, np.floating):

            if np.isnan(value):
                return None

            return float(value)

        if isinstance(value, np.ndarray):
            return value.tolist()

        if isinstance(value, dict):

            return {
                str(key):
                    AdvancedPanels._json_safe(val)
                for key, val in value.items()
            }

        if isinstance(value, (list, tuple)):

            return [
                AdvancedPanels._json_safe(item)
                for item in value
            ]

        return value

    # ========================================================
    # MAIN RENDERER
    # ========================================================

    @staticmethod
    def render(
        results: dict[str, Any],
        dataframe: pd.DataFrame,
    ) -> None:

        if dataframe is None or dataframe.empty:

            st.info(
                "Upload a dataset to activate "
                "NEXUS intelligence."
            )

            return

        if not isinstance(results, dict):
            results = {}

        df = dataframe.copy()

        # ----------------------------------------------------
        # RESULT CONTRACT
        # ----------------------------------------------------

        version = AdvancedPanels._safe_get(
            results,
            "version",
            "N/A",
        )

        metadata = AdvancedPanels._safe_get(
            results,
            "metadata",
            {},
        )

        health = AdvancedPanels._safe_get(
            results,
            "health",
            {},
        )

        quality = AdvancedPanels._safe_get(
            results,
            "quality",
            {},
        )

        schema = AdvancedPanels._safe_get(
            results,
            "schema",
            {},
        )

        correlations = AdvancedPanels._safe_get(
            results,
            "correlations",
            pd.DataFrame(),
        )

        outliers = AdvancedPanels._safe_get(
            results,
            "outliers",
            {},
        )

        drivers = AdvancedPanels._safe_get(
            results,
            "drivers",
            {},
        )

        distributions = AdvancedPanels._safe_get(
            results,
            "distributions",
            {},
        )

        target_analysis = AdvancedPanels._safe_get(
            results,
            "target_analysis",
            {},
        )

        risks = AdvancedPanels._safe_get(
            results,
            "risks",
            [],
        )

        kpis = AdvancedPanels._safe_get(
            results,
            "kpis",
            {},
        )

        ml_readiness = AdvancedPanels._safe_get(
            results,
            "ml_readiness",
            {},
        )

        executive_summary = AdvancedPanels._safe_get(
            results,
            "executive_summary",
            [],
        )

        recommendations = AdvancedPanels._safe_get(
            results,
            "recommendations",
            [],
        )

        decision_intelligence_result = (
            AdvancedPanels._safe_get(
                results,
                "decision_intelligence",
                {},
            )
        )

        numeric_columns = (
            AdvancedPanels._safe_get(
                results,
                "numeric_columns",
                [],
            )
        )

        categorical_columns = (
            AdvancedPanels._safe_get(
                results,
                "categorical_columns",
                [],
            )
        )

        datetime_columns = (
            AdvancedPanels._safe_get(
                results,
                "datetime_columns",
                [],
            )
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        st.markdown(
            """
            <div style="
                padding: 1.5rem;
                border-radius: 16px;
                margin-bottom: 1.5rem;
                border: 1px solid rgba(120,120,120,0.25);
            ">
                <h1 style="margin:0;">
                    🧠 NEXUS AI Intelligence Center
                </h1>
                <p style="
                    margin-top:0.5rem;
                    font-size:1.05rem;
                ">
                    Autonomous Enterprise Analytics,
                    Decision Intelligence & Risk Detection
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ====================================================
        # EXECUTIVE SCORECARD
        # ====================================================

        st.header(
            "🎯 Executive Intelligence"
        )

        total_rows = len(df)
        total_columns = len(df.columns)

        missing_values = int(
            df.isna().sum().sum()
        )

        duplicate_rows = int(
            df.duplicated().sum()
        )

        health_score = None

        if isinstance(health, dict):

            for key in (
                "score",
                "health_score",
                "overall_score",
            ):

                if key in health:

                    health_score = health[key]

                    break

        score_display = (
            AdvancedPanels._format_number(
                health_score,
                1,
            )
            if health_score is not None
            else "N/A"
        )

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "Rows",
            f"{total_rows:,}",
        )

        c2.metric(
            "Columns",
            f"{total_columns:,}",
        )

        c3.metric(
            "Numeric Fields",
            f"{len(numeric_columns):,}",
        )

        c4.metric(
            "Missing Cells",
            f"{missing_values:,}",
        )

        c5.metric(
            "Health Score",
            score_display,
        )

        # ====================================================
        # TABS
        # ====================================================

        tabs = st.tabs(
            [
                "📊 Overview",
                "📋 Dataset",
                "🧹 Quality",
                "📈 EDA",
                "🔗 Relationships",
                "🚨 Anomalies",
                "🎯 Root Cause",
                "🤖 ML Readiness",
                "🧠 AI Insights",
                "💼 Decisions",
                "⚠️ Risks",
                "📦 Export",
            ]
        )

        # ====================================================
        # TAB 0 — OVERVIEW
        # ====================================================

        with tabs[0]:

            st.subheader(
                "🧑‍💼 Executive Summary"
            )

            if isinstance(
                executive_summary,
                str,
            ):

                st.info(
                    executive_summary
                )

            elif isinstance(
                executive_summary,
                (list, tuple),
            ):

                if executive_summary:

                    for index, item in enumerate(
                        executive_summary,
                        start=1,
                    ):

                        st.info(
                            f"**Finding {index}**\n\n"
                            f"{item}"
                        )

                else:

                    st.info(
                        "No executive findings generated."
                    )

            elif isinstance(
                executive_summary,
                dict,
            ):

                for key, value in (
                    executive_summary.items()
                ):

                    st.info(
                        f"**{key}:** {value}"
                    )

            # --------------------------------------------
            # KPI CARDS
            # --------------------------------------------

            st.subheader(
                "💰 Business KPI Intelligence"
            )

            if isinstance(
                kpis,
                dict
            ) and kpis:

                items = list(
                    kpis.items()
                )[:8]

                columns = st.columns(
                    min(
                        len(items),
                        4,
                    )
                )

                for index, (
                    name,
                    value,
                ) in enumerate(items):

                    column = columns[
                        index % len(columns)
                    ]

                    label = (
                        str(name)
                        .replace(
                            "_",
                            " ",
                        )
                        .title()
                    )

                    if (
                        "margin"
                        in str(name).lower()
                    ):

                        display_value = (
                            f"{float(value):.2f}%"
                            if isinstance(
                                value,
                                (
                                    int,
                                    float,
                                    np.number,
                                ),
                            )
                            else str(value)
                        )

                    elif isinstance(
                        value,
                        (
                            int,
                            float,
                            np.number,
                        ),
                    ):

                        display_value = (
                            AdvancedPanels._format_number(
                                value
                            )
                        )

                    else:

                        display_value = str(
                            value
                        )

                    column.metric(
                        label,
                        display_value,
                    )

            else:

                st.info(
                    "No automatic KPIs were detected."
                )

            # --------------------------------------------
            # METADATA
            # --------------------------------------------

            if isinstance(
                metadata,
                dict
            ) and metadata:

                with st.expander(
                    "ℹ️ Analysis Metadata"
                ):

                    metadata_rows = [
                        {
                            "Property": key,
                            "Value": value,
                        }
                        for key, value
                        in metadata.items()
                    ]

                    st.dataframe(
                        pd.DataFrame(
                            metadata_rows
                        ),
                        width="stretch",
                        hide_index=True,
                    )

        # ====================================================
        # TAB 1 — DATASET
        # ====================================================

        with tabs[1]:

            st.subheader(
                "📋 Dataset Preview"
            )

            st.dataframe(
                df.head(200),
                width="stretch",
                height=450,
            )

            st.subheader(
                "🧬 Schema Intelligence"
            )

            schema_rows = []

            for column in df.columns:

                series = df[column]

                schema_rows.append(
                    {
                        "Column": column,
                        "Data Type": str(
                            series.dtype
                        ),
                        "Non-Null": int(
                            series.notna().sum()
                        ),
                        "Missing": int(
                            series.isna().sum()
                        ),
                        "Unique": int(
                            series.nunique(
                                dropna=True
                            )
                        ),
                        "Missing %": round(
                            series.isna().mean()
                            * 100,
                            2,
                        ),
                    }
                )

            schema_df = pd.DataFrame(
                schema_rows
            )

            st.dataframe(
                schema_df,
                width="stretch",
                hide_index=True,
            )

            st.subheader(
                "📐 Dataset Statistics"
            )

            try:

                statistics = (
                    df.describe(
                        include="all"
                    )
                    .transpose()
                )

                st.dataframe(
                    statistics,
                    width="stretch",
                )

            except Exception as error:

                st.warning(
                    f"Statistics unavailable: {error}"
                )

        # ====================================================
        # TAB 2 — QUALITY
        # ====================================================

        with tabs[2]:

            st.subheader(
                "🧹 Data Quality Intelligence"
            )

            q1, q2, q3, q4 = st.columns(4)

            q1.metric(
                "Missing Cells",
                f"{missing_values:,}",
            )

            q2.metric(
                "Duplicate Rows",
                f"{duplicate_rows:,}",
            )

            q3.metric(
                "Columns With Missing",
                f"{int((df.isna().sum() > 0).sum()):,}",
            )

            q4.metric(
                "Rows",
                f"{len(df):,}",
            )

            missing = (
                df.isna()
                .sum()
                .sort_values(
                    ascending=False
                )
            )

            missing = missing[
                missing > 0
            ]

            if not missing.empty:

                missing_df = (
                    missing
                    .reset_index()
                )

                missing_df.columns = [
                    "Column",
                    "Missing Values",
                ]

                missing_df[
                    "Missing %"
                ] = (
                    missing_df[
                        "Missing Values"
                    ]
                    / len(df)
                    * 100
                ).round(2)

                st.dataframe(
                    missing_df,
                    width="stretch",
                    hide_index=True,
                )

                figure = px.bar(
                    missing_df,
                    x="Column",
                    y="Missing Values",
                    title="Missing Values by Column",
                )

                st.plotly_chart(
                    figure,
                    width="stretch",
                )

            else:

                st.success(
                    "✅ No missing values detected."
                )

            if duplicate_rows:

                st.warning(
                    f"⚠️ {duplicate_rows:,} duplicate "
                    "rows detected."
                )

            else:

                st.success(
                    "✅ No duplicate rows detected."
                )

            quality_df = (
                AdvancedPanels._to_dataframe(
                    quality
                )
            )

            if not quality_df.empty:

                st.subheader(
                    "Engine Quality Report"
                )

                st.dataframe(
                    quality_df,
                    width="stretch",
                    hide_index=True,
                )

        # ====================================================
        # TAB 3 — EDA
        # ====================================================

        with tabs[3]:

            st.subheader(
                "📈 Exploratory Data Analysis"
            )

            if numeric_columns:

                selected_metric = st.selectbox(
                    "Numerical Metric",
                    numeric_columns,
                    key="advanced_eda_metric",
                )

                metric_series = pd.to_numeric(
                    df[selected_metric],
                    errors="coerce",
                ).dropna()

                if not metric_series.empty:

                    fig = px.histogram(
                        x=metric_series,
                        nbins=30,
                        marginal="box",
                        title=(
                            f"Distribution of "
                            f"{selected_metric}"
                        ),
                    )

                    st.plotly_chart(
                        fig,
                        width="stretch",
                    )

                    e1, e2, e3, e4 = st.columns(4)

                    e1.metric(
                        "Mean",
                        AdvancedPanels._format_number(
                            metric_series.mean()
                        ),
                    )

                    e2.metric(
                        "Median",
                        AdvancedPanels._format_number(
                            metric_series.median()
                        ),
                    )

                    e3.metric(
                        "Std Dev",
                        AdvancedPanels._format_number(
                            metric_series.std()
                        ),
                    )

                    e4.metric(
                        "Unique",
                        f"{metric_series.nunique():,}",
                    )

            else:

                st.info(
                    "No numerical metrics available."
                )

            # --------------------------------------------
            # CATEGORY ANALYSIS
            # --------------------------------------------

            if (
                numeric_columns
                and categorical_columns
            ):

                st.divider()

                c1, c2 = st.columns(2)

                with c1:

                    dimension = st.selectbox(
                        "Business Dimension",
                        categorical_columns,
                        key="advanced_dimension",
                    )

                with c2:

                    metric = st.selectbox(
                        "Business Metric",
                        numeric_columns,
                        key="advanced_metric",
                    )

                try:

                    grouped = (
                        df
                        .assign(
                            _metric=pd.to_numeric(
                                df[metric],
                                errors="coerce",
                            )
                        )
                        .groupby(
                            dimension,
                            dropna=False,
                        )["_metric"]
                        .sum()
                        .sort_values(
                            ascending=False
                        )
                        .reset_index()
                    )

                    figure = px.bar(
                        grouped,
                        x=dimension,
                        y="_metric",
                        title=(
                            f"{metric} by "
                            f"{dimension}"
                        ),
                    )

                    st.plotly_chart(
                        figure,
                        width="stretch",
                    )

                except Exception as error:

                    st.warning(
                        f"EDA failed: {error}"
                    )

            # --------------------------------------------
            # TIME ANALYSIS
            # --------------------------------------------

            if (
                datetime_columns
                and numeric_columns
            ):

                st.divider()

                st.subheader(
                    "⏱️ Time Intelligence"
                )

                date_column = st.selectbox(
                    "Date Column",
                    datetime_columns,
                    key="advanced_date",
                )

                time_metric = st.selectbox(
                    "Time Metric",
                    numeric_columns,
                    key="advanced_time_metric",
                )

                try:

                    temp = df.copy()

                    temp[
                        date_column
                    ] = pd.to_datetime(
                        temp[date_column],
                        errors="coerce",
                    )

                    temp[
                        time_metric
                    ] = pd.to_numeric(
                        temp[time_metric],
                        errors="coerce",
                    )

                    temp = temp.dropna(
                        subset=[
                            date_column,
                            time_metric,
                        ]
                    )

                    if not temp.empty:

                        time_data = (
                            temp
                            .groupby(
                                date_column
                            )[time_metric]
                            .sum()
                            .reset_index()
                            .sort_values(
                                date_column
                            )
                        )

                        figure = px.line(
                            time_data,
                            x=date_column,
                            y=time_metric,
                            markers=True,
                            title=(
                                f"{time_metric} over time"
                            ),
                        )

                        st.plotly_chart(
                            figure,
                            width="stretch",
                        )

                    else:

                        st.info(
                            "No valid time-series data."
                        )

                except Exception as error:

                    st.warning(
                        f"Time analysis failed: {error}"
                    )

        # ====================================================
        # TAB 4 — RELATIONSHIPS
        # ====================================================

        with tabs[4]:

            st.subheader(
                "🔗 Relationship Intelligence"
            )

            if len(numeric_columns) >= 2:

                try:

                    corr_matrix = (
                        df[numeric_columns]
                        .corr()
                    )

                    heatmap = go.Figure(
                        data=go.Heatmap(
                            z=corr_matrix.values,
                            x=corr_matrix.columns,
                            y=corr_matrix.columns,
                            text=np.round(
                                corr_matrix.values,
                                2,
                            ),
                            texttemplate="%{text}",
                            zmin=-1,
                            zmax=1,
                        )
                    )

                    heatmap.update_layout(
                        title="Correlation Heatmap",
                        height=600,
                    )

                    st.plotly_chart(
                        heatmap,
                        width="stretch",
                    )

                except Exception as error:

                    st.warning(
                        f"Correlation heatmap failed: {error}"
                    )

            else:

                st.info(
                    "At least two numeric columns "
                    "are required."
                )

            correlation_df = (
                AdvancedPanels._to_dataframe(
                    correlations
                )
            )

            if not correlation_df.empty:

                st.subheader(
                    "Strongest Relationships"
                )

                st.dataframe(
                    correlation_df,
                    width="stretch",
                    hide_index=True,
                )

        # ====================================================
        # TAB 5 — ANOMALIES
        # ====================================================

        with tabs[5]:

            st.subheader(
                "🚨 Anomaly Intelligence"
            )

            if numeric_columns:

                anomaly_column = st.selectbox(
                    "Metric to investigate",
                    numeric_columns,
                    key="advanced_anomaly_metric",
                )

                if st.button(
                    "🔍 Run Anomaly Investigation",
                    key="advanced_anomaly_button",
                    type="primary",
                ):

                    try:

                        detector = (
                            AnomalyDetector()
                        )

                        anomaly_data = (
                            detector.detect(
                                df,
                                anomaly_column,
                            )
                        )

                        st.session_state[
                            "advanced_anomaly_results"
                        ] = anomaly_data

                    except Exception as error:

                        st.error(
                            f"Anomaly detection failed: {error}"
                        )

                anomaly_data = (
                    st.session_state.get(
                        "advanced_anomaly_results"
                    )
                )

                if isinstance(
                    anomaly_data,
                    pd.DataFrame,
                ):

                    if "anomaly" in anomaly_data.columns:

                        anomaly_count = int(
                            anomaly_data[
                                "anomaly"
                            ].sum()
                        )

                        if anomaly_count > 0:

                            st.warning(
                                f"🚨 {anomaly_count:,} "
                                "potential anomalies detected."
                            )

                            anomaly_rows = (
                                anomaly_data[
                                    anomaly_data[
                                        "anomaly"
                                    ]
                                    == True
                                ]
                            )

                            st.dataframe(
                                anomaly_rows,
                                width="stretch",
                                hide_index=True,
                            )

                        else:

                            st.success(
                                "✅ No significant anomalies detected."
                            )

                    else:

                        st.dataframe(
                            anomaly_data,
                            width="stretch",
                        )

                # Engine outlier information

                outlier_df = (
                    AdvancedPanels._to_dataframe(
                        outliers
                    )
                )

                if not outlier_df.empty:

                    st.subheader(
                        "Engine Outlier Report"
                    )

                    st.dataframe(
                        outlier_df,
                        width="stretch",
                        hide_index=True,
                    )

            else:

                st.info(
                    "No numeric columns available."
                )

        # ====================================================
        # TAB 6 — ROOT CAUSE
        # ====================================================

        with tabs[6]:

            st.subheader(
                "🎯 Root Cause & Driver Intelligence"
            )

            if isinstance(
                drivers,
                dict
            ) and drivers:

                driver_df = (
                    AdvancedPanels._to_dataframe(
                        drivers
                    )
                )

                if not driver_df.empty:

                    st.dataframe(
                        driver_df,
                        width="stretch",
                        hide_index=True,
                    )

                else:

                    st.json(
                        AdvancedPanels._json_safe(
                            drivers
                        )
                    )

            else:

                st.info(
                    "No root-cause drivers were generated."
                )

            st.subheader(
                "🎯 Target Analysis"
            )

            if isinstance(
                target_analysis,
                dict
            ) and target_analysis:

                target_df = (
                    AdvancedPanels._to_dataframe(
                        target_analysis
                    )
                )

                if not target_df.empty:

                    st.dataframe(
                        target_df,
                        width="stretch",
                        hide_index=True,
                    )

            else:

                st.info(
                    "No target analysis available."
                )

        # ====================================================
        # TAB 7 — ML READINESS
        # ====================================================

        with tabs[7]:

            st.subheader(
                "🤖 Machine Learning Readiness"
            )

            if isinstance(
                ml_readiness,
                dict
            ) and ml_readiness:

                readiness_rows = []

                for key, value in (
                    ml_readiness.items()
                ):

                    readiness_rows.append(
                        {
                            "Assessment": (
                                str(key)
                                .replace(
                                    "_",
                                    " ",
                                )
                                .title()
                            ),
                            "Value": value,
                        }
                    )

                st.dataframe(
                    pd.DataFrame(
                        readiness_rows
                    ),
                    width="stretch",
                    hide_index=True,
                )

            else:

                st.info(
                    "ML readiness information unavailable."
                )

        # ====================================================
        # TAB 8 — AI INSIGHTS
        # ====================================================

        with tabs[8]:

            st.subheader(
                "🧠 Autonomous AI Findings"
            )

            if isinstance(
                executive_summary,
                list
            ) and executive_summary:

                for index, finding in enumerate(
                    executive_summary,
                    start=1,
                ):

                    st.markdown(
                        f"""
                        <div style="
                            padding:1rem;
                            margin-bottom:0.8rem;
                            border-radius:12px;
                            border:1px solid rgba(120,120,120,0.25);
                        ">
                            <strong>
                                Finding {index}
                            </strong>
                            <br><br>
                            {finding}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            if (
                isinstance(
                    recommendations,
                    list,
                )
                and recommendations
            ):

                st.subheader(
                    "💡 Strategic Recommendations"
                )

                for index, recommendation in enumerate(
                    recommendations,
                    start=1,
                ):

                    st.success(
                        f"**Recommendation {index}:** "
                        f"{recommendation}"
                    )

            # --------------------------------------------
            # STATISTICAL OBSERVATIONS
            # --------------------------------------------

            if numeric_columns:

                st.subheader(
                    "🔬 Statistical Observations"
                )

                try:

                    stats = (
                        df[numeric_columns]
                        .describe()
                        .T
                    )

                    mean_values = (
                        stats["mean"]
                        .replace(
                            0,
                            np.nan,
                        )
                    )

                    stats[
                        "coefficient_of_variation"
                    ] = (
                        stats["std"]
                        / mean_values
                    )

                    st.dataframe(
                        stats.round(4),
                        width="stretch",
                    )

                except Exception as error:

                    st.warning(
                        f"Statistical analysis failed: {error}"
                    )

        # ====================================================
        # TAB 9 — DECISION INTELLIGENCE
        # ====================================================

        with tabs[9]:

            AdvancedPanels.decision_intelligence(
                results,
                df,
            )

        # ====================================================
        # TAB 10 — RISKS
        # ====================================================

        with tabs[10]:

            st.subheader(
                "⚠️ Enterprise Risk Intelligence"
            )

            if isinstance(
                risks,
                list
            ) and risks:

                for index, risk in enumerate(
                    risks,
                    start=1,
                ):

                    if isinstance(
                        risk,
                        dict,
                    ):

                        severity = str(
                            risk.get(
                                "severity",
                                "UNKNOWN",
                            )
                        )

                        message = risk.get(
                            "message",
                            str(risk),
                        )

                        if severity.upper() == "HIGH":

                            st.error(
                                f"🔴 **Risk {index} — "
                                f"{severity}**\n\n"
                                f"{message}"
                            )

                        elif severity.upper() == "MEDIUM":

                            st.warning(
                                f"🟠 **Risk {index} — "
                                f"{severity}**\n\n"
                                f"{message}"
                            )

                        else:

                            st.info(
                                f"🔵 **Risk {index} — "
                                f"{severity}**\n\n"
                                f"{message}"
                            )

                    else:

                        st.warning(
                            f"**Risk {index}:** {risk}"
                        )

            elif isinstance(
                risks,
                dict,
            ) and risks:

                risk_df = (
                    AdvancedPanels._to_dataframe(
                        risks
                    )
                )

                if not risk_df.empty:

                    st.dataframe(
                        risk_df,
                        width="stretch",
                        hide_index=True,
                    )

                else:

                    st.json(
                        AdvancedPanels._json_safe(
                            risks
                        )
                    )

            else:

                st.success(
                    "✅ No significant risks reported."
                )

        # ====================================================
        # TAB 11 — EXPORT
        # ====================================================

        with tabs[11]:

            st.subheader(
                "📦 NEXUS Intelligence Export Center"
            )

            cleaned_csv = (
                df.to_csv(
                    index=False
                ).encode("utf-8")
            )

            st.download_button(
                "⬇️ Download Dataset CSV",
                data=cleaned_csv,
                file_name="nexus_dataset.csv",
                mime="text/csv",
                width="stretch",
            )

            json_report = json.dumps(
                AdvancedPanels._json_safe(
                    results
                ),
                indent=2,
                default=str,
            )

            st.download_button(
                "⬇️ Download Full Intelligence JSON",
                data=json_report.encode(
                    "utf-8"
                ),
                file_name="nexus_intelligence_report.json",
                mime="application/json",
                width="stretch",
            )

            # --------------------------------------------
            # CSV CORRELATIONS
            # --------------------------------------------

            correlation_export = (
                AdvancedPanels._to_dataframe(
                    correlations
                )
            )

            if not correlation_export.empty:

                st.download_button(
                    "⬇️ Download Correlation Report",
                    data=correlation_export.to_csv(
                        index=False
                    ).encode("utf-8"),
                    file_name="nexus_correlations.csv",
                    mime="text/csv",
                    width="stretch",
                )

            # --------------------------------------------
            # METADATA
            # --------------------------------------------

            st.write(
                f"**Engine Version:** {version}"
            )

            st.write(
                f"**Generated:** "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

    # ========================================================
    # DECISION INTELLIGENCE
    # ========================================================

    @staticmethod
    def decision_intelligence(
        results: dict[str, Any],
        dataframe: pd.DataFrame | None = None,
    ) -> None:

        st.header(
            "🧠 Decision Intelligence"
        )

        if (
            dataframe is None
            or dataframe.empty
        ):

            st.info(
                "Upload a dataset to activate "
                "decision intelligence."
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
        # COLUMN DETECTION
        # ----------------------------------------------------

        revenue_candidates = (
            AdvancedPanels._find_columns(
                dataframe,
                [
                    "revenue",
                    "sales",
                    "income",
                    "turnover",
                    "amount",
                ],
            )
        )

        profit_candidates = (
            AdvancedPanels._find_columns(
                dataframe,
                [
                    "profit",
                    "earnings",
                    "net_income",
                    "net profit",
                ],
            )
        )

        col1, col2 = st.columns(2)

        with col1:

            revenue_column = st.selectbox(
                "Revenue / Sales Metric",
                revenue_candidates
                if revenue_candidates
                else numeric_columns,
                key="decision_revenue_column",
            )

        with col2:

            profit_column = st.selectbox(
                "Profit Metric",
                profit_candidates
                if profit_candidates
                else numeric_columns,
                key="decision_profit_column",
            )

        revenue = float(
            pd.to_numeric(
                dataframe[
                    revenue_column
                ],
                errors="coerce",
            )
            .fillna(0)
            .sum()
        )

        profit = float(
            pd.to_numeric(
                dataframe[
                    profit_column
                ],
                errors="coerce",
            )
            .fillna(0)
            .sum()
        )

        margin = (
            profit / revenue * 100
            if revenue != 0
            else 0
        )

        # ----------------------------------------------------
        # CURRENT BUSINESS STATE
        # ----------------------------------------------------

        st.divider()

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Current Revenue",
            AdvancedPanels._currency(
                revenue
            ),
        )

        c2.metric(
            "Current Profit",
            AdvancedPanels._currency(
                profit
            ),
        )

        c3.metric(
            "Profit Margin",
            f"{margin:.2f}%",
        )

        # ----------------------------------------------------
        # SIMULATOR
        # ----------------------------------------------------

        st.markdown(
            "### 🎛️ What-If Business Simulator"
        )

        st.caption(
            "Test strategic assumptions before making a decision."
        )

        s1, s2 = st.columns(2)

        with s1:

            price = st.slider(
                "Price Change (%)",
                -50.0,
                50.0,
                0.0,
                1.0,
                key="decision_price",
            )

            demand = st.slider(
                "Demand Change (%)",
                -80.0,
                100.0,
                0.0,
                1.0,
                key="decision_demand",
            )

            marketing = st.slider(
                "Marketing Change (%)",
                -100.0,
                300.0,
                0.0,
                5.0,
                key="decision_marketing",
            )

        with s2:

            variable_cost = st.slider(
                "Variable Cost Change (%)",
                -50.0,
                100.0,
                0.0,
                1.0,
                key="decision_variable_cost",
            )

            fixed_cost = st.slider(
                "Fixed Cost Change (%)",
                -50.0,
                100.0,
                0.0,
                1.0,
                key="decision_fixed_cost",
            )

        # ----------------------------------------------------
        # DECISION ENGINE
        # ----------------------------------------------------

        try:

            from app.analytics.decision_engine import (
                DecisionEngine,
                Scenario,
            )

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
                    revenue,
                    profit,
                    scenario,
                )
            )

            new_revenue = float(
                simulation.get(
                    "revenue",
                    revenue,
                )
            )

            new_profit = float(
                simulation.get(
                    "profit",
                    profit,
                )
            )

            revenue_change = float(
                simulation.get(
                    "revenue_change_pct",
                    0,
                )
            )

            profit_change = float(
                simulation.get(
                    "profit_change_pct",
                    0,
                )
            )

            projected_margin = (
                new_profit
                / new_revenue
                * 100
                if new_revenue != 0
                else 0
            )

            # --------------------------------------------
            # RESULT CARDS
            # --------------------------------------------

            st.divider()

            st.markdown(
                "### 📊 Simulation Result"
            )

            r1, r2, r3, r4 = st.columns(4)

            r1.metric(
                "Projected Revenue",
                AdvancedPanels._currency(
                    new_revenue
                ),
                f"{revenue_change:+.2f}%",
            )

            r2.metric(
                "Projected Profit",
                AdvancedPanels._currency(
                    new_profit
                ),
                f"{profit_change:+.2f}%",
            )

            r3.metric(
                "Projected Margin",
                f"{projected_margin:.2f}%",
            )

            r4.metric(
                "Profit Delta",
                AdvancedPanels._currency(
                    new_profit - profit
                ),
            )

            # --------------------------------------------
            # RECOMMENDATION
            # --------------------------------------------

            if new_profit > profit:

                st.success(
                    "🟢 **NEXUS Recommendation:** "
                    "This scenario increases projected profit."
                )

            elif new_profit < profit:

                st.error(
                    "🔴 **NEXUS Warning:** "
                    "This scenario decreases projected profit."
                )

            else:

                st.info(
                    "🟡 This scenario produces approximately "
                    "the same projected profit."
                )

            # --------------------------------------------
            # COMPARISON
            # --------------------------------------------

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
                        (
                            projected_margin
                            - margin
                        ),
                    ],
                }
            )

            st.dataframe(
                comparison,
                width="stretch",
                hide_index=True,
            )

            # --------------------------------------------
            # VISUAL COMPARISON
            # --------------------------------------------

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

            # --------------------------------------------
            # ENGINE RESULT
            # --------------------------------------------

            if (
                isinstance(
                    results.get(
                        "decision_intelligence"
                    ),
                    dict,
                )
            ):

                with st.expander(
                    "🔬 Engine Decision Intelligence"
                ):

                    st.json(
                        AdvancedPanels._json_safe(
                            results.get(
                                "decision_intelligence"
                            )
                        )
                    )

        except ImportError:

            st.error(
                "Decision engine module is not available. "
                "Check app/analytics/decision_engine.py."
            )

        except Exception as error:

            st.error(
                f"Decision engine failed: {error}"
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