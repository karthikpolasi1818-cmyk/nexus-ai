from __future__ import annotations

from typing import Any

import pandas as pd


class CopilotAgent:
    """
    NEXUS AI Executive Copilot.

    A deterministic, dataset-aware analytical assistant.
    It answers questions using the results already produced
    by the NEXUS analytical pipeline.
    """

    def __init__(
        self,
        dataframe: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None
    ):

        self.dataframe = dataframe
        self.results = results or {}

    # =========================================================
    # PUBLIC API
    # =========================================================

    def ask(self, question: str) -> dict[str, Any]:

        question = (question or "").strip()

        if not question:

            return self._response(
                "Please enter a question about your dataset.",
                "general"
            )

        if (
            self.dataframe is None
            or self.dataframe.empty
        ):

            return self._response(
                "No dataset is currently available.",
                "general"
            )

        normalized = question.lower()

        # -----------------------------------------------------
        # INTENT ROUTING
        # -----------------------------------------------------

        if self._contains(
            normalized,
            [
                "why",
                "reason",
                "cause",
                "caused",
                "driver"
            ]
        ):

            response = self._why_question(
                question
            )

            if response:
                return response

        if self._contains(
            normalized,
            [
                "anomal",
                "outlier",
                "unusual",
                "abnormal"
            ]
        ):

            response = self._anomaly_question()

            if response:
                return response

        if self._contains(
            normalized,
            [
                "correlation",
                "related",
                "relationship"
            ]
        ):

            response = self._correlation_question()

            if response:
                return response

        if self._contains(
            normalized,
            [
                "revenue",
                "sales"
            ]
        ):

            response = self._revenue_question()

            if response:
                return response

        if self._contains(
            normalized,
            [
                "profit",
                "margin",
                "earnings"
            ]
        ):

            response = self._profit_question()

            if response:
                return response

        if self._contains(
            normalized,
            [
                "best",
                "top",
                "highest",
                "maximum"
            ]
        ):

            response = self._best_question()

            if response:
                return response

        if self._contains(
            normalized,
            [
                "worst",
                "lowest",
                "minimum",
                "bottom"
            ]
        ):

            response = self._worst_question()

            if response:
                return response

        if self._contains(
            normalized,
            [
                "quality",
                "missing",
                "duplicate",
                "clean"
            ]
        ):

            response = self._quality_question()

            if response:
                return response

        if self._contains(
            normalized,
            [
                "forecast",
                "predict",
                "future"
            ]
        ):

            response = self._forecast_question()

            if response:
                return response

        if self._contains(
            normalized,
            [
                "recommend",
                "recommendation",
                "should",
                "focus",
                "action"
            ]
        ):

            response = self._recommendation_question()

            if response:
                return response

        if self._contains(
            normalized,
            [
                "summary",
                "overview",
                "overall",
                "business"
            ]
        ):

            return self.executive_summary()

        return self._general_question(
            question
        )

    # =========================================================
    # EXECUTIVE SUMMARY
    # =========================================================

    def executive_summary(self) -> dict[str, Any]:

        profile = self.results.get(
            "profile",
            {}
        )

        health = self.results.get(
            "health",
            {}
        )

        summary_parts = []

        rows = profile.get(
            "rows",
            len(self.dataframe)
        )

        columns = profile.get(
            "columns",
            len(self.dataframe.columns)
        )

        summary_parts.append(
            f"The dataset contains {rows:,} rows "
            f"across {columns} columns."
        )

        if isinstance(health, dict):

            score = health.get(
                "score"
            )

            if score is not None:

                summary_parts.append(
                    f"Overall data health is "
                    f"{float(score):.1f}/100."
                )

        kpis = self.results.get(
            "kpis",
            {}
        )

        if isinstance(kpis, dict):

            revenue = self._find_kpi(
                kpis,
                [
                    "TOTAL_REVENUE",
                    "REVENUE",
                    "SALES"
                ]
            )

            profit = self._find_kpi(
                kpis,
                [
                    "TOTAL_PROFIT",
                    "PROFIT"
                ]
            )

            if revenue is not None:

                summary_parts.append(
                    f"Detected revenue/sales is "
                    f"{self._money(revenue)}."
                )

            if profit is not None:

                summary_parts.append(
                    f"Detected profit is "
                    f"{self._money(profit)}."
                )

        risks = self.results.get(
            "risks",
            []
        )

        if risks:

            summary_parts.append(
                f"NEXUS identified {len(risks)} "
                f"potential risk indicators."
            )

        return self._response(
            " ".join(summary_parts),
            "executive_summary"
        )

    # =========================================================
    # WHY / ROOT CAUSE
    # =========================================================

    def _why_question(
        self,
        question: str
    ) -> dict[str, Any] | None:

        drivers = self.results.get(
            "drivers",
            {}
        )

        if not drivers:

            return None

        if isinstance(drivers, dict):

            ranked = []

            for key, value in drivers.items():

                try:

                    numeric_value = abs(
                        float(value)
                    )

                    ranked.append(
                        (
                            key,
                            numeric_value,
                            value
                        )
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    continue

            ranked.sort(
                key=lambda x: x[1],
                reverse=True
            )

            if ranked:

                findings = []

                for (
                    feature,
                    _,
                    value
                ) in ranked[:5]:

                    findings.append(
                        f"{feature}: {value}"
                    )

                return self._response(
                    "The strongest detected drivers are: "
                    + "; ".join(findings)
                    + ". These are statistical relationships, "
                    "not proof of causation.",
                    "root_cause",
                    findings
                )

        return None

    # =========================================================
    # ANOMALIES
    # =========================================================

    def _anomaly_question(
        self
    ) -> dict[str, Any] | None:

        outliers = self.results.get(
            "outliers",
            {}
        )

        if outliers is None:

            return None

        if isinstance(
            outliers,
            pd.DataFrame
        ):

            if outliers.empty:

                return self._response(
                    "No significant outlier records were "
                    "returned by the current analysis.",
                    "anomaly"
                )

            return self._response(
                f"NEXUS identified {len(outliers):,} "
                "potential anomalous records.",
                "anomaly"
            )

        if isinstance(outliers, dict):

            if not outliers:

                return self._response(
                    "No significant anomalies were "
                    "returned by the current analysis.",
                    "anomaly"
                )

            return self._response(
                f"NEXUS has anomaly information for "
                f"{len(outliers)} metrics.",
                "anomaly"
            )

        return None

    # =========================================================
    # CORRELATION
    # =========================================================

    def _correlation_question(
        self
    ) -> dict[str, Any] | None:

        correlations = self.results.get(
            "correlations"
        )

        if correlations is None:

            return None

        if isinstance(
            correlations,
            pd.DataFrame
        ):

            if correlations.empty:

                return self._response(
                    "There are not enough numeric variables "
                    "to identify meaningful correlations.",
                    "correlation"
                )

            top = correlations.head(5)

            findings = []

            for _, row in top.iterrows():

                a = row.get(
                    "feature_a",
                    "Feature A"
                )

                b = row.get(
                    "feature_b",
                    "Feature B"
                )

                corr = row.get(
                    "correlation",
                    0
                )

                findings.append(
                    f"{a} ↔ {b}: "
                    f"{float(corr):.3f}"
                )

            return self._response(
                "The strongest detected relationships are: "
                + "; ".join(findings)
                + ". Correlation does not establish causation.",
                "correlation",
                findings
            )

        return None

    # =========================================================
    # REVENUE
    # =========================================================

    def _revenue_question(
        self
    ) -> dict[str, Any] | None:

        column = self._find_column(
            [
                "revenue",
                "sales",
                "turnover",
                "income"
            ]
        )

        if column is None:

            return None

        series = pd.to_numeric(
            self.dataframe[column],
            errors="coerce"
        ).dropna()

        if series.empty:

            return None

        total = float(
            series.sum()
        )

        average = float(
            series.mean()
        )

        maximum = float(
            series.max()
        )

        minimum = float(
            series.min()
        )

        return self._response(
            f"Using `{column}` as the detected "
            f"revenue/sales metric: total is "
            f"{self._money(total)}, average is "
            f"{self._money(average)}, maximum is "
            f"{self._money(maximum)}, and minimum is "
            f"{self._money(minimum)}.",
            "revenue",
            [
                f"Metric: {column}",
                f"Total: {self._money(total)}",
                f"Average: {self._money(average)}"
            ]
        )

    # =========================================================
    # PROFIT
    # =========================================================

    def _profit_question(
        self
    ) -> dict[str, Any] | None:

        column = self._find_column(
            [
                "profit",
                "earnings",
                "net_income"
            ]
        )

        if column is None:

            return None

        series = pd.to_numeric(
            self.dataframe[column],
            errors="coerce"
        ).dropna()

        if series.empty:

            return None

        total_profit = float(
            series.sum()
        )

        revenue_column = self._find_column(
            [
                "revenue",
                "sales",
                "turnover"
            ]
        )

        margin = None

        if revenue_column:

            revenue = pd.to_numeric(
                self.dataframe[
                    revenue_column
                ],
                errors="coerce"
            ).sum()

            if revenue:

                margin = (
                    total_profit
                    / float(revenue)
                    * 100
                )

        message = (
            f"Detected profit metric `{column}` "
            f"has total profit of "
            f"{self._money(total_profit)}."
        )

        if margin is not None:

            message += (
                f" The calculated overall profit "
                f"margin is {margin:.2f}%."
            )

        return self._response(
            message,
            "profit"
        )

    # =========================================================
    # BEST
    # =========================================================

    def _best_question(
        self
    ) -> dict[str, Any] | None:

        categorical = (
            self.dataframe
            .select_dtypes(
                exclude="number"
            )
            .columns
            .tolist()
        )

        metric = self._find_column(
            [
                "revenue",
                "sales",
                "profit",
                "income"
            ]
        )

        if not categorical or metric is None:

            return None

        grouped = (
            self.dataframe
            .assign(
                _metric=pd.to_numeric(
                    self.dataframe[metric],
                    errors="coerce"
                )
            )
            .groupby(
                categorical[0],
                dropna=False
            )["_metric"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        if grouped.empty:

            return None

        best = grouped.index[0]

        value = grouped.iloc[0]

        return self._response(
            f"The strongest detected "
            f"{categorical[0]} by total {metric} "
            f"is `{best}`, with "
            f"{self._money(value)}.",
            "ranking"
        )

    # =========================================================
    # WORST
    # =========================================================

    def _worst_question(
        self
    ) -> dict[str, Any] | None:

        categorical = (
            self.dataframe
            .select_dtypes(
                exclude="number"
            )
            .columns
            .tolist()
        )

        metric = self._find_column(
            [
                "revenue",
                "sales",
                "profit",
                "income"
            ]
        )

        if not categorical or metric is None:

            return None

        grouped = (
            self.dataframe
            .assign(
                _metric=pd.to_numeric(
                    self.dataframe[metric],
                    errors="coerce"
                )
            )
            .groupby(
                categorical[0],
                dropna=False
            )["_metric"]
            .sum()
            .sort_values()
        )

        if grouped.empty:

            return None

        worst = grouped.index[0]

        value = grouped.iloc[0]

        return self._response(
            f"The weakest detected "
            f"{categorical[0]} by total {metric} "
            f"is `{worst}`, with "
            f"{self._money(value)}.",
            "ranking"
        )

    # =========================================================
    # QUALITY
    # =========================================================

    def _quality_question(
        self
    ) -> dict[str, Any] | None:

        missing = int(
            self.dataframe
            .isna()
            .sum()
            .sum()
        )

        duplicates = int(
            self.dataframe
            .duplicated()
            .sum()
        )

        message = (
            f"The dataset currently contains "
            f"{missing:,} missing cells and "
            f"{duplicates:,} duplicate rows."
        )

        if missing:

            message += (
                " Missing-value treatment should be "
                "reviewed before production modeling."
            )

        return self._response(
            message,
            "quality"
        )

    # =========================================================
    # FORECAST
    # =========================================================

    def _forecast_question(
        self
    ) -> dict[str, Any] | None:

        forecast = self.results.get(
            "forecast"
        )

        if forecast is None:

            forecast = self.results.get(
                "forecasting"
            )

        if forecast is None:

            return self._response(
                "Forecasting is not currently available "
                "for this analysis. A valid date column and "
                "suitable numeric metric may be required.",
                "forecast"
            )

        return self._response(
            "Forecasting results are available in the "
            "Predictive Intelligence section of NEXUS.",
            "forecast"
        )

    # =========================================================
    # RECOMMENDATIONS
    # =========================================================

    def _recommendation_question(
        self
    ) -> dict[str, Any] | None:

        recommendations = self.results.get(
            "recommendations",
            []
        )

        if not recommendations:

            return self._response(
                "NEXUS does not currently have enough "
                "evidence to generate a specific recommendation.",
                "recommendation"
            )

        if isinstance(
            recommendations,
            dict
        ):

            recommendations = list(
                recommendations.values()
            )

        findings = [
            str(item)
            for item in recommendations[:5]
        ]

        return self._response(
            "Based on the current analytical results, "
            "NEXUS recommends: "
            + " ".join(findings),
            "recommendation",
            findings
        )

    # =========================================================
    # GENERAL QUESTION
    # =========================================================

    def _general_question(
        self,
        question: str
    ) -> dict[str, Any]:

        numeric = (
            self.dataframe
            .select_dtypes(
                include="number"
            )
            .columns
            .tolist()
        )

        categorical = (
            self.dataframe
            .select_dtypes(
                exclude="number"
            )
            .columns
            .tolist()
        )

        return self._response(
            f"I can analyze `{question}` using the "
            f"available dataset. Currently I can answer "
            f"questions about revenue, profit, rankings, "
            f"anomalies, correlations, data quality, "
            f"forecasting and recommendations. "
            f"The dataset contains {len(numeric)} numeric "
            f"and {len(categorical)} categorical columns.",
            "general"
        )

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _contains(
        text: str,
        words: list[str]
    ) -> bool:

        return any(
            word in text
            for word in words
        )

    def _find_column(
        self,
        keywords: list[str]
    ) -> str | None:

        columns = list(
            self.dataframe.columns
        )

        for keyword in keywords:

            for column in columns:

                if keyword in str(
                    column
                ).lower():

                    return column

        return None

    @staticmethod
    def _find_kpi(
        kpis: dict,
        candidates: list[str]
    ):

        for candidate in candidates:

            if candidate in kpis:

                try:
                    return float(
                        kpis[candidate]
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    return kpis[candidate]

        return None

    @staticmethod
    def _money(
        value: float
    ) -> str:

        try:

            return f"₹{float(value):,.2f}"

        except (
            TypeError,
            ValueError
        ):

            return str(value)

    @staticmethod
    def _response(
        answer: str,
        intent: str,
        findings: list[str] | None = None
    ) -> dict[str, Any]:

        return {
            "answer": answer,
            "intent": intent,
            "findings": findings or [],
            "source": "NEXUS Analytical Engine"
        }