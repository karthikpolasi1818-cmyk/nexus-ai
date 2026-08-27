from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


# ============================================================
# NEXUS AI — INSIGHT PANEL
# ============================================================


class InsightPanel:
    """
    Executive-level presentation layer for NEXUS AI insights.

    Handles:
    - Executive summary
    - Overall business status
    - Critical findings
    - Warnings
    - Positive findings
    - Recommendations
    - Detailed insight table
    """

    # ========================================================
    # SAFE HELPERS
    # ========================================================

    @staticmethod
    def _safe_text(
        value: Any,
        default: str = "",
    ) -> str:

        if value is None:
            return default

        if isinstance(value, str):
            return value

        return str(value)

    @staticmethod
    def _safe_number(
        value: Any,
        default: float = 0.0,
    ) -> float:

        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _get(
        results: dict[str, Any],
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
    # STATUS
    # ========================================================

    @staticmethod
    def _status_config(
        status: str,
    ) -> tuple[str, str]:

        status = status.lower().strip()

        if status == "critical":
            return "🔴", "Critical Attention Required"

        if status == "warning":
            return "🟠", "Management Attention Required"

        if status == "positive":
            return "🟢", "Positive Business Signals"

        return "🔵", "Analysis Completed"

    # ========================================================
    # INSIGHT CARD
    # ========================================================

    @classmethod
    def _render_insight(
        cls,
        insight: dict[str, Any],
    ) -> None:

        if not isinstance(insight, dict):
            return

        severity = cls._safe_text(
            insight.get(
                "severity",
                "info",
            )
        ).lower()

        title = cls._safe_text(
            insight.get(
                "title",
                "Business Insight",
            )
        )

        message = cls._safe_text(
            insight.get(
                "message",
                "",
            )
        )

        category = cls._safe_text(
            insight.get(
                "category",
                "General",
            )
        )

        recommendation = cls._safe_text(
            insight.get(
                "recommendation",
                "",
            )
        )

        metric = cls._safe_text(
            insight.get(
                "metric",
                "",
            )
        )

        value = insight.get(
            "value"
        )

        if severity == "critical":

            icon = "🔴"

        elif severity == "warning":

            icon = "🟠"

        elif severity == "positive":

            icon = "🟢"

        else:

            icon = "🔵"

        with st.container(border=True):

            st.markdown(
                f"### {icon} {title}"
            )

            st.caption(
                f"Category: {category}"
            )

            if message:

                st.write(
                    message
                )

            if metric:

                if isinstance(
                    value,
                    (int, float),
                ):

                    st.metric(
                        metric,
                        f"{value:,.2f}",
                    )

                else:

                    st.caption(
                        f"Metric: {metric}"
                    )

            if recommendation:

                st.info(
                    f"💡 **Recommendation:** "
                    f"{recommendation}"
                )

    # ========================================================
    # SUMMARY METRICS
    # ========================================================

    @classmethod
    def _render_metrics(
        cls,
        results: dict[str, Any],
    ) -> None:

        total = int(
            cls._safe_number(
                cls._get(
                    results,
                    "total_insights",
                    0,
                )
            )
        )

        critical = int(
            cls._safe_number(
                cls._get(
                    results,
                    "critical_count",
                    0,
                )
            )
        )

        warnings = int(
            cls._safe_number(
                cls._get(
                    results,
                    "warning_count",
                    0,
                )
            )
        )

        positive = int(
            cls._safe_number(
                cls._get(
                    results,
                    "positive_count",
                    0,
                )
            )
        )

        info = int(
            cls._safe_number(
                cls._get(
                    results,
                    "info_count",
                    0,
                )
            )
        )

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "Total Insights",
            total,
        )

        c2.metric(
            "Critical",
            critical,
        )

        c3.metric(
            "Warnings",
            warnings,
        )

        c4.metric(
            "Positive",
            positive,
        )

        c5.metric(
            "Informational",
            info,
        )

    # ========================================================
    # RECOMMENDATIONS
    # ========================================================

    @classmethod
    def _render_recommendations(
        cls,
        results: dict[str, Any],
    ) -> None:

        recommendations = cls._get(
            results,
            "recommendations",
            [],
        )

        if not isinstance(
            recommendations,
            list,
        ):

            recommendations = []

        st.markdown(
            "### 🎯 Strategic Recommendations"
        )

        if not recommendations:

            st.info(
                "No strategic recommendations were generated."
            )

            return

        for index, recommendation in enumerate(
            recommendations,
            start=1,
        ):

            text = cls._safe_text(
                recommendation
            )

            if not text:
                continue

            st.markdown(
                f"**{index}.** {text}"
            )

    # ========================================================
    # INSIGHT TABLE
    # ========================================================

    @classmethod
    def _render_table(
        cls,
        results: dict[str, Any],
    ) -> None:

        insights = cls._get(
            results,
            "insights",
            [],
        )

        if not isinstance(
            insights,
            list,
        ):

            insights = []

        if not insights:
            return

        rows = []

        for insight in insights:

            if not isinstance(
                insight,
                dict,
            ):
                continue

            rows.append(
                {
                    "Category": cls._safe_text(
                        insight.get(
                            "category"
                        )
                    ),
                    "Severity": cls._safe_text(
                        insight.get(
                            "severity"
                        )
                    ).upper(),
                    "Title": cls._safe_text(
                        insight.get(
                            "title"
                        )
                    ),
                    "Message": cls._safe_text(
                        insight.get(
                            "message"
                        )
                    ),
                    "Metric": cls._safe_text(
                        insight.get(
                            "metric"
                        )
                    ),
                }
            )

        if not rows:
            return

        table = pd.DataFrame(
            rows
        )

        st.markdown(
            "### 📋 All Generated Insights"
        )

        st.dataframe(
            table,
            width="stretch",
            hide_index=True,
        )

    # ========================================================
    # MAIN RENDER
    # ========================================================

    @classmethod
    def render(
        cls,
        results: dict[str, Any] | None,
        dataframe: pd.DataFrame | None = None,
    ) -> None:

        st.subheader(
            "🧠 NEXUS AI — Executive Intelligence"
        )

        if not isinstance(
            results,
            dict,
        ):

            st.info(
                "No intelligence results are available yet."
            )

            return

        # ----------------------------------------------------
        # EXECUTIVE SUMMARY
        # ----------------------------------------------------

        summary = cls._safe_text(
            cls._get(
                results,
                "executive_summary",
                "No executive summary is available.",
            )
        )

        status = cls._safe_text(
            cls._get(
                results,
                "overall_status",
                "info",
            )
        )

        icon, status_text = (
            cls._status_config(
                status
            )
        )

        st.markdown(
            "### 📌 Executive Summary"
        )

        with st.container(
            border=True
        ):

            st.markdown(
                f"## {icon} {status_text}"
            )

            st.write(
                summary
            )

        # ----------------------------------------------------
        # METRICS
        # ----------------------------------------------------

        cls._render_metrics(
            results
        )

        st.divider()

        # ----------------------------------------------------
        # CRITICAL INSIGHTS
        # ----------------------------------------------------

        critical = cls._get(
            results,
            "critical_insights",
            [],
        )

        if isinstance(
            critical,
            list
        ) and critical:

            st.markdown(
                "### 🔴 Critical Findings"
            )

            for insight in critical:

                cls._render_insight(
                    insight
                )

        # ----------------------------------------------------
        # WARNINGS
        # ----------------------------------------------------

        warnings = cls._get(
            results,
            "warnings",
            [],
        )

        if isinstance(
            warnings,
            list
        ) and warnings:

            st.markdown(
                "### 🟠 Warnings"
            )

            for insight in warnings:

                cls._render_insight(
                    insight
                )

        # ----------------------------------------------------
        # POSITIVE
        # ----------------------------------------------------

        positive = cls._get(
            results,
            "positive_insights",
            [],
        )

        if isinstance(
            positive,
            list
        ) and positive:

            st.markdown(
                "### 🟢 Positive Signals"
            )

            for insight in positive:

                cls._render_insight(
                    insight
                )

        # ----------------------------------------------------
        # INFORMATIONAL
        # ----------------------------------------------------

        info = cls._get(
            results,
            "info_insights",
            [],
        )

        if isinstance(
            info,
            list
        ) and info:

            with st.expander(
                "🔵 Informational Insights"
            ):

                for insight in info:

                    cls._render_insight(
                        insight
                    )

        st.divider()

        # ----------------------------------------------------
        # RECOMMENDATIONS
        # ----------------------------------------------------

        cls._render_recommendations(
            results
        )

        st.divider()

        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------

        cls._render_table(
            results
        )


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================

def render_insight_panel(
    results: dict[str, Any] | None,
    dataframe: pd.DataFrame | None = None,
) -> None:

    InsightPanel.render(
        results=results,
        dataframe=dataframe,
    )