from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import numpy as np
import pandas as pd


# ============================================================
# NEXUS AI — INSIGHT ENGINE
# ============================================================


@dataclass
class Insight:
    category: str
    title: str
    message: str
    severity: str = "info"
    metric: str | None = None
    value: Any = None
    recommendation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class InsightEngine:
    """
    Converts analytical results and business data into
    structured executive-level insights.

    The engine is intentionally defensive:
    - Handles missing columns
    - Handles empty DataFrames
    - Handles NaN / infinity
    - Handles numeric and categorical data
    - Does not assume a fixed dataset schema
    """

    # ========================================================
    # SAFE HELPERS
    # ========================================================

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            number = float(value)

            if not np.isfinite(number):
                return default

            return number

        except (TypeError, ValueError):
            return default

    @staticmethod
    def _find_column(
        dataframe: pd.DataFrame,
        keywords: list[str],
    ) -> str | None:

        if dataframe.empty:
            return None

        for column in dataframe.columns:

            column_text = str(column).lower().strip()

            if any(
                keyword.lower() in column_text
                for keyword in keywords
            ):
                return column

        return None

    @staticmethod
    def _numeric_columns(
        dataframe: pd.DataFrame,
    ) -> list[str]:

        if dataframe.empty:
            return []

        return (
            dataframe
            .select_dtypes(include="number")
            .columns
            .tolist()
        )

    @staticmethod
    def _clean_numeric_series(
        series: pd.Series,
    ) -> pd.Series:

        return pd.to_numeric(
            series,
            errors="coerce",
        ).replace(
            [np.inf, -np.inf],
            np.nan,
        ).dropna()

    # ========================================================
    # DATA QUALITY INSIGHTS
    # ========================================================

    @staticmethod
    def data_quality_insights(
        dataframe: pd.DataFrame,
    ) -> list[Insight]:

        insights: list[Insight] = []

        if dataframe is None or dataframe.empty:
            insights.append(
                Insight(
                    category="Data Quality",
                    title="Dataset is empty",
                    message=(
                        "NEXUS could not generate business insights "
                        "because the dataset contains no usable rows."
                    ),
                    severity="critical",
                    recommendation=(
                        "Upload a dataset containing valid business records."
                    ),
                )
            )

            return insights

        rows = len(dataframe)
        columns = len(dataframe.columns)

        missing_cells = int(
            dataframe.isna().sum().sum()
        )

        duplicate_rows = int(
            dataframe.duplicated().sum()
        )

        total_cells = rows * columns

        missing_pct = (
            missing_cells / total_cells * 100
            if total_cells
            else 0
        )

        if missing_pct == 0:

            insights.append(
                Insight(
                    category="Data Quality",
                    title="Data completeness is strong",
                    message=(
                        f"The dataset contains {rows:,} rows and "
                        f"{columns:,} columns with no missing values."
                    ),
                    severity="positive",
                    metric="Missing Data",
                    value=0,
                )
            )

        elif missing_pct < 5:

            insights.append(
                Insight(
                    category="Data Quality",
                    title="Minor missing-data issue",
                    message=(
                        f"{missing_pct:.2f}% of dataset cells are missing."
                    ),
                    severity="warning",
                    metric="Missing Data",
                    value=round(missing_pct, 2),
                    recommendation=(
                        "Review missing values before using the data "
                        "for high-impact decisions."
                    ),
                )
            )

        else:

            insights.append(
                Insight(
                    category="Data Quality",
                    title="Significant missing data detected",
                    message=(
                        f"{missing_pct:.2f}% of dataset cells are missing."
                    ),
                    severity="critical",
                    metric="Missing Data",
                    value=round(missing_pct, 2),
                    recommendation=(
                        "Investigate the source of missing records and "
                        "apply an appropriate imputation or cleaning strategy."
                    ),
                )
            )

        if duplicate_rows > 0:

            duplicate_pct = (
                duplicate_rows / rows * 100
            )

            insights.append(
                Insight(
                    category="Data Quality",
                    title="Duplicate records detected",
                    message=(
                        f"{duplicate_rows:,} duplicate rows were detected "
                        f"({duplicate_pct:.2f}% of the dataset)."
                    ),
                    severity="warning",
                    metric="Duplicates",
                    value=duplicate_rows,
                    recommendation=(
                        "Validate whether duplicate records represent "
                        "legitimate repeated transactions before removing them."
                    ),
                )
            )

        return insights

    # ========================================================
    # BUSINESS METRIC INSIGHTS
    # ========================================================

    @classmethod
    def business_insights(
        cls,
        dataframe: pd.DataFrame,
    ) -> list[Insight]:

        insights: list[Insight] = []

        if dataframe is None or dataframe.empty:
            return insights

        revenue_column = cls._find_column(
            dataframe,
            [
                "revenue",
                "sales",
                "turnover",
                "income",
            ],
        )

        profit_column = cls._find_column(
            dataframe,
            [
                "profit",
                "earnings",
                "net_income",
                "net profit",
            ],
        )

        quantity_column = cls._find_column(
            dataframe,
            [
                "quantity",
                "units",
                "volume",
                "qty",
            ],
        )

        # ----------------------------------------------------
        # REVENUE
        # ----------------------------------------------------

        if revenue_column is not None:

            revenue_series = cls._clean_numeric_series(
                dataframe[revenue_column]
            )

            if not revenue_series.empty:

                total_revenue = revenue_series.sum()
                average_revenue = revenue_series.mean()

                insights.append(
                    Insight(
                        category="Business Performance",
                        title="Revenue baseline established",
                        message=(
                            f"Total {revenue_column} is "
                            f"{total_revenue:,.2f}, with an average "
                            f"of {average_revenue:,.2f} per record."
                        ),
                        severity="positive",
                        metric=revenue_column,
                        value=round(
                            float(total_revenue),
                            2,
                        ),
                    )
                )

                if len(revenue_series) >= 3:

                    highest = revenue_series.max()
                    lowest = revenue_series.min()

                    if lowest != 0:

                        spread = (
                            (highest - lowest)
                            / abs(lowest)
                            * 100
                        )

                    else:
                        spread = 0

                    if spread > 100:

                        insights.append(
                            Insight(
                                category="Business Performance",
                                title="Revenue variability is high",
                                message=(
                                    f"The difference between the highest "
                                    f"and lowest observed {revenue_column} "
                                    f"is approximately {spread:.1f}%."
                                ),
                                severity="warning",
                                metric=revenue_column,
                                value=round(spread, 2),
                                recommendation=(
                                    "Investigate the records driving the "
                                    "largest revenue variation."
                                ),
                            )
                        )

        # ----------------------------------------------------
        # PROFIT
        # ----------------------------------------------------

        if profit_column is not None:

            profit_series = cls._clean_numeric_series(
                dataframe[profit_column]
            )

            if not profit_series.empty:

                total_profit = profit_series.sum()

                if total_profit > 0:

                    insights.append(
                        Insight(
                            category="Profitability",
                            title="Positive aggregate profitability",
                            message=(
                                f"Aggregate {profit_column} is "
                                f"{total_profit:,.2f}."
                            ),
                            severity="positive",
                            metric=profit_column,
                            value=round(
                                float(total_profit),
                                2,
                            ),
                        )
                    )

                elif total_profit < 0:

                    insights.append(
                        Insight(
                            category="Profitability",
                            title="Aggregate loss detected",
                            message=(
                                f"Aggregate {profit_column} is "
                                f"{total_profit:,.2f}."
                            ),
                            severity="critical",
                            metric=profit_column,
                            value=round(
                                float(total_profit),
                                2,
                            ),
                            recommendation=(
                                "Investigate cost structure, pricing, "
                                "and the segments contributing most to losses."
                            ),
                        )
                    )

                else:

                    insights.append(
                        Insight(
                            category="Profitability",
                            title="Profit is approximately neutral",
                            message=(
                                "Aggregate profit is approximately zero."
                            ),
                            severity="warning",
                            metric=profit_column,
                            value=0,
                        )
                    )

        # ----------------------------------------------------
        # PROFIT MARGIN
        # ----------------------------------------------------

        if (
            revenue_column is not None
            and profit_column is not None
        ):

            revenue_series = cls._clean_numeric_series(
                dataframe[revenue_column]
            )

            profit_series = cls._clean_numeric_series(
                dataframe[profit_column]
            )

            revenue_total = revenue_series.sum()
            profit_total = profit_series.sum()

            if revenue_total != 0:

                margin = (
                    profit_total
                    / revenue_total
                    * 100
                )

                if margin >= 20:

                    severity = "positive"

                elif margin >= 10:

                    severity = "info"

                elif margin >= 0:

                    severity = "warning"

                else:

                    severity = "critical"

                insights.append(
                    Insight(
                        category="Profitability",
                        title="Profit margin analyzed",
                        message=(
                            f"Estimated aggregate profit margin is "
                            f"{margin:.2f}%."
                        ),
                        severity=severity,
                        metric="Profit Margin",
                        value=round(
                            float(margin),
                            2,
                        ),
                        recommendation=(
                            "Protect high-margin revenue streams and "
                            "investigate low-margin segments."
                        )
                        if margin < 20
                        else (
                            "Maintain pricing discipline and protect "
                            "the current margin structure."
                        ),
                    )
                )

        # ----------------------------------------------------
        # QUANTITY
        # ----------------------------------------------------

        if quantity_column is not None:

            quantity_series = cls._clean_numeric_series(
                dataframe[quantity_column]
            )

            if not quantity_series.empty:

                total_quantity = quantity_series.sum()

                insights.append(
                    Insight(
                        category="Operations",
                        title="Volume baseline established",
                        message=(
                            f"Total recorded {quantity_column} is "
                            f"{total_quantity:,.2f}."
                        ),
                        severity="info",
                        metric=quantity_column,
                        value=round(
                            float(total_quantity),
                            2,
                        ),
                    )
                )

        return insights

    # ========================================================
    # SEGMENT INSIGHTS
    # ========================================================

    @classmethod
    def segment_insights(
        cls,
        dataframe: pd.DataFrame,
    ) -> list[Insight]:

        insights: list[Insight] = []

        if dataframe is None or dataframe.empty:
            return insights

        numeric_columns = cls._numeric_columns(
            dataframe
        )

        if not numeric_columns:
            return insights

        metric_column = cls._find_column(
            dataframe,
            [
                "revenue",
                "sales",
                "profit",
                "income",
            ],
        )

        if metric_column is None:
            metric_column = numeric_columns[0]

        metric = pd.to_numeric(
            dataframe[metric_column],
            errors="coerce",
        )

        working = dataframe.copy()

        working["_nexus_metric"] = metric

        categorical_columns = (
            working
            .select_dtypes(
                exclude="number"
            )
            .columns
            .tolist()
        )

        for column in categorical_columns[:5]:

            if column == "_nexus_metric":
                continue

            groups = (
                working
                .groupby(
                    column,
                    dropna=False,
                )["_nexus_metric"]
                .sum()
                .sort_values(
                    ascending=False
                )
            )

            if len(groups) < 2:
                continue

            groups = groups.dropna()

            if groups.empty:
                continue

            top_segment = groups.index[0]
            top_value = cls._safe_float(
                groups.iloc[0]
            )

            total_value = cls._safe_float(
                groups.sum()
            )

            if total_value == 0:
                continue

            share = (
                top_value
                / total_value
                * 100
            )

            if share >= 50:

                insights.append(
                    Insight(
                        category="Segmentation",
                        title=f"{column} concentration detected",
                        message=(
                            f"'{top_segment}' contributes approximately "
                            f"{share:.1f}% of total {metric_column}."
                        ),
                        severity="warning",
                        metric=metric_column,
                        value=round(
                            float(share),
                            2,
                        ),
                        recommendation=(
                            f"Review dependency on the '{top_segment}' "
                            f"{column} segment and assess diversification opportunities."
                        ),
                    )
                )

            else:

                insights.append(
                    Insight(
                        category="Segmentation",
                        title=f"{column} leader identified",
                        message=(
                            f"'{top_segment}' is the leading {column} "
                            f"segment for {metric_column}, contributing "
                            f"approximately {share:.1f}%."
                        ),
                        severity="info",
                        metric=metric_column,
                        value=round(
                            float(share),
                            2,
                        ),
                    )
                )

        return insights

    # ========================================================
    # TREND INSIGHTS
    # ========================================================

    @classmethod
    def trend_insights(
        cls,
        dataframe: pd.DataFrame,
    ) -> list[Insight]:

        insights: list[Insight] = []

        if dataframe is None or dataframe.empty:
            return insights

        date_column = None

        for column in dataframe.columns:

            column_text = str(column).lower()

            if (
                "date" in column_text
                or "time" in column_text
                or "month" in column_text
                or "year" in column_text
            ):

                converted = pd.to_datetime(
                    dataframe[column],
                    errors="coerce",
                )

                if converted.notna().sum() >= 2:
                    date_column = column
                    break

        if date_column is None:
            return insights

        metric_column = cls._find_column(
            dataframe,
            [
                "revenue",
                "sales",
                "profit",
            ],
        )

        if metric_column is None:
            numeric = cls._numeric_columns(
                dataframe
            )

            if not numeric:
                return insights

            metric_column = numeric[0]

        working = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    dataframe[date_column],
                    errors="coerce",
                ),
                "metric": pd.to_numeric(
                    dataframe[metric_column],
                    errors="coerce",
                ),
            }
        ).dropna()

        if len(working) < 3:
            return insights

        working = working.sort_values(
            "date"
        )

        midpoint = len(working) // 2

        first_half = working.iloc[:midpoint]
        second_half = working.iloc[midpoint:]

        if first_half.empty or second_half.empty:
            return insights

        first_mean = first_half["metric"].mean()
        second_mean = second_half["metric"].mean()

        if first_mean == 0:
            return insights

        change_pct = (
            (second_mean - first_mean)
            / abs(first_mean)
            * 100
        )

        if change_pct > 10:

            severity = "positive"
            title = "Positive trend detected"
            recommendation = (
                "Investigate the drivers of recent growth "
                "and determine whether the trend is sustainable."
            )

        elif change_pct < -10:

            severity = "critical"
            title = "Negative trend detected"
            recommendation = (
                "Investigate the recent decline and identify "
                "the products, regions, or channels responsible."
            )

        else:

            severity = "info"
            title = "Trend is relatively stable"
            recommendation = (
                "Continue monitoring the metric for emerging changes."
            )

        insights.append(
            Insight(
                category="Trend Analysis",
                title=title,
                message=(
                    f"{metric_column} changed by approximately "
                    f"{change_pct:+.2f}% between the earlier and "
                    f"later portions of the dataset."
                ),
                severity=severity,
                metric=metric_column,
                value=round(
                    float(change_pct),
                    2,
                ),
                recommendation=recommendation,
            )
        )

        return insights

    # ========================================================
    # MASTER ENGINE
    # ========================================================

    @classmethod
    def generate(
        cls,
        dataframe: pd.DataFrame,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        if dataframe is None:
            dataframe = pd.DataFrame()

        if not isinstance(results, dict):
            results = {}

        insights: list[Insight] = []

        insights.extend(
            cls.data_quality_insights(
                dataframe
            )
        )

        insights.extend(
            cls.business_insights(
                dataframe
            )
        )

        insights.extend(
            cls.segment_insights(
                dataframe
            )
        )

        insights.extend(
            cls.trend_insights(
                dataframe
            )
        )

        critical = [
            item.to_dict()
            for item in insights
            if item.severity == "critical"
        ]

        warnings = [
            item.to_dict()
            for item in insights
            if item.severity == "warning"
        ]

        positive = [
            item.to_dict()
            for item in insights
            if item.severity == "positive"
        ]

        info = [
            item.to_dict()
            for item in insights
            if item.severity == "info"
        ]

        # ----------------------------------------------------
        # EXECUTIVE SUMMARY
        # ----------------------------------------------------

        if critical:

            executive_summary = (
                "NEXUS identified critical business or data-quality "
                "issues requiring immediate investigation."
            )

            overall_status = "critical"

        elif warnings:

            executive_summary = (
                "NEXUS identified important areas requiring "
                "management attention while overall performance "
                "remains actionable."
            )

            overall_status = "warning"

        elif positive:

            executive_summary = (
                "NEXUS identified positive business signals "
                "with no major issues detected by the current analysis."
            )

            overall_status = "positive"

        else:

            executive_summary = (
                "NEXUS completed the analysis but found insufficient "
                "evidence for strong business conclusions."
            )

            overall_status = "info"

        # ----------------------------------------------------
        # RECOMMENDATIONS
        # ----------------------------------------------------

        recommendations = []

        for insight in insights:

            recommendation = insight.recommendation

            if (
                recommendation
                and recommendation not in recommendations
            ):

                recommendations.append(
                    recommendation
                )

        # ----------------------------------------------------
        # SAFE RESULT
        # ----------------------------------------------------

        return {
            "executive_summary": executive_summary,
            "overall_status": overall_status,
            "total_insights": len(insights),
            "critical_count": len(critical),
            "warning_count": len(warnings),
            "positive_count": len(positive),
            "info_count": len(info),
            "insights": [
                insight.to_dict()
                for insight in insights
            ],
            "critical_insights": critical,
            "warnings": warnings,
            "positive_insights": positive,
            "info_insights": info,
            "recommendations": recommendations,
        }


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================

def generate_insights(
    dataframe: pd.DataFrame,
    results: dict[str, Any] | None = None,
) -> dict[str, Any]:

    return InsightEngine.generate(
        dataframe=dataframe,
        results=results,
    )