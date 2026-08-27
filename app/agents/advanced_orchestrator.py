# app/agents/advanced_orchestrator.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from app.analytics.advanced_intelligence import (
    AdvancedIntelligence,
)

from app.analytics.root_cause import (
    root_cause_analysis,
)

from app.analytics.decision_intelligence import (
    DecisionIntelligence,
)
class AdvancedNexusOrchestrator:
    """
    Advanced orchestration layer for NEXUS AI.

    Responsibilities:
    - Dataset profiling
    - Data quality analysis
    - Schema detection
    - Correlation intelligence
    - Outlier detection
    - Root-cause analysis
    - Distribution analysis
    - Target analysis
    - Risk detection
    - KPI generation
    - ML readiness assessment
    - Executive summary
    - Business recommendations
    """

    VERSION = "3.0.0"

    # =========================================================
    # PUBLIC EXECUTION
    # =========================================================

    def execute(
        self,
        df: pd.DataFrame,
        target: str | None = None,
    ) -> dict[str, Any]:

        if df is None:
            raise ValueError("NEXUS received no dataset.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError(
                "NEXUS expects a pandas DataFrame."
            )

        if df.empty:
            raise ValueError(
                "NEXUS received an empty dataset."
            )

        # Work on a copy so the original dataframe
        # is never unexpectedly modified.
        data = df.copy()

        # Clean column names for safer downstream processing.
        data.columns = [
            str(column).strip()
            for column in data.columns
        ]

        # Resolve target safely.
        resolved_target = self._resolve_target(
            data,
            target
        )

        # -----------------------------------------------------
        # COLUMN TYPES
        # -----------------------------------------------------

        numeric_columns = (
            data
            .select_dtypes(
                include=np.number
            )
            .columns
            .tolist()
        )

        categorical_columns = (
            data
            .select_dtypes(
                exclude=np.number
            )
            .columns
            .tolist()
        )

        datetime_columns = (
            self._detect_datetime_columns(
                data
            )
        )

        # -----------------------------------------------------
        # METADATA
        # -----------------------------------------------------

        metadata = self._metadata(
            data,
            resolved_target
        )

        # -----------------------------------------------------
        # DATA QUALITY
        # -----------------------------------------------------

        quality = self._safe_quality_report(
            data
        )

        # -----------------------------------------------------
        # SCHEMA
        # -----------------------------------------------------

        schema = self._safe_schema(
            data
        )

        # -----------------------------------------------------
        # HEALTH
        # -----------------------------------------------------

        health = self._health_score(
            data
        )

        # -----------------------------------------------------
        # CORRELATIONS
        # -----------------------------------------------------

        correlations = self._correlations(
            data,
            numeric_columns
        )

        # -----------------------------------------------------
        # OUTLIERS
        # -----------------------------------------------------

        outliers = self._outliers(
            data,
            numeric_columns
        )

        # -----------------------------------------------------
        # ROOT CAUSE / DRIVERS
        # -----------------------------------------------------

        drivers: dict[str, Any] = {}

        if resolved_target is not None:

            try:

                drivers = root_cause_analysis(
                    data,
                    resolved_target
                )

            except Exception as error:

                drivers = {
                    "status": "unavailable",
                    "target": resolved_target,
                    "error": str(error)
                }

        # -----------------------------------------------------
        # DISTRIBUTIONS
        # -----------------------------------------------------

        distributions = self._distributions(
            data,
            numeric_columns
        )

        # -----------------------------------------------------
        # TARGET ANALYSIS
        # -----------------------------------------------------

        target_analysis = self._target_analysis(
            data,
            resolved_target
        )

        # -----------------------------------------------------
        # RISKS
        # -----------------------------------------------------

        risks = self._risks(
            data,
            numeric_columns,
            categorical_columns
        )

        # -----------------------------------------------------
        # KPIs
        # -----------------------------------------------------

        kpis = self._kpis(
            data,
            numeric_columns
        )

        # -----------------------------------------------------
        # ML READINESS
        # -----------------------------------------------------

        ml_readiness = self._ml_readiness(
            data,
            resolved_target
        )

        # -----------------------------------------------------
        # EXECUTIVE SUMMARY
        # -----------------------------------------------------

        executive_summary = (
            self._executive_summary(
                data=data,
                target=resolved_target,
                health=health,
                risks=risks,
                outliers=outliers,
                correlations=correlations,
                target_analysis=target_analysis,
                ml_readiness=ml_readiness
            )
        )

        # -----------------------------------------------------
        # RECOMMENDATIONS
        # -----------------------------------------------------

        recommendations = (
            self._recommendations(
                data=data,
                target=resolved_target,
                health=health,
                risks=risks,
                outliers=outliers,
                correlations=correlations,
                target_analysis=target_analysis,
                ml_readiness=ml_readiness
            )
        )

        # -----------------------------------------------------
        # FINAL RESULT
        # -----------------------------------------------------

        return {

            "version":
                self.VERSION,

            "metadata":
                metadata,

            "health":
                health,

            "quality":
                quality,

            "schema":
                schema,

            "correlations":
                correlations,

            "outliers":
                outliers,

            "drivers":
                drivers,

            "distributions":
                distributions,

            "target_analysis":
                target_analysis,

            "risks":
                risks,

            "kpis":
                kpis,

            "ml_readiness":
                ml_readiness,

            "executive_summary":
                executive_summary,

            "recommendations":
                recommendations,

            "numeric_columns":
                numeric_columns,

            "categorical_columns":
                categorical_columns,

            "datetime_columns":
                datetime_columns,
        }

    # =========================================================
    # TARGET DETECTION
    # =========================================================

    @staticmethod
    def _resolve_target(
        df: pd.DataFrame,
        target: str | None
    ) -> str | None:

        if target:

            if target in df.columns:
                return target

            # Case-insensitive matching.
            target_lower = target.lower()

            for column in df.columns:

                if str(column).lower() == target_lower:
                    return column

        # Automatic business target detection.
        preferred_names = [

            "sales",
            "revenue",
            "profit",
            "income",
            "amount",
            "target",
            "y"
        ]

        for preferred in preferred_names:

            for column in df.columns:

                if str(column).lower() == preferred:
                    return column

        return None

    # =========================================================
    # METADATA
    # =========================================================

    @staticmethod
    def _metadata(
        df: pd.DataFrame,
        target: str | None
    ) -> dict[str, Any]:

        memory_mb = (
            df.memory_usage(
                deep=True
            ).sum()
            / 1024
            / 1024
        )

        return {

            "rows":
                int(df.shape[0]),

            "columns":
                int(df.shape[1]),

            "total_cells":
                int(
                    df.shape[0]
                    * df.shape[1]
                ),

            "target":
                target,

            "duplicate_rows":
                int(
                    df.duplicated().sum()
                ),

            "memory_mb":
                round(
                    float(memory_mb),
                    2
                ),

            "generated_at":
                datetime.now().isoformat(
                    timespec="seconds"
                )
        }

    # =========================================================
    # QUALITY
    # =========================================================

    @staticmethod
    def _safe_quality_report(
        df: pd.DataFrame
    ) -> Any:

        try:

            result = (
                AdvancedIntelligence
                .quality_report(df)
            )

            if isinstance(
                result,
                pd.DataFrame
            ):

                return result.to_dict(
                    orient="records"
                )

            return result

        except Exception as error:

            missing = (
                df.isna()
                .sum()
                .sort_values(
                    ascending=False
                )
            )

            return {

                "error":
                    str(error),

                "missing_values":
                    missing.to_dict(),

                "duplicate_rows":
                    int(
                        df.duplicated().sum()
                    )
            }

    # =========================================================
    # SCHEMA
    # =========================================================

    @staticmethod
    def _safe_schema(
        df: pd.DataFrame
    ) -> Any:

        try:

            result = (
                AdvancedIntelligence
                .schema(df)
            )

            if isinstance(
                result,
                pd.DataFrame
            ):

                return result.to_dict(
                    orient="records"
                )

            return result

        except Exception:

            schema = []

            for column in df.columns:

                schema.append({

                    "column":
                        column,

                    "dtype":
                        str(
                            df[column].dtype
                        ),

                    "missing":
                        int(
                            df[column]
                            .isna()
                            .sum()
                        ),

                    "unique":
                        int(
                            df[column]
                            .nunique(
                                dropna=True
                            )
                        )
                })

            return schema

    # =========================================================
    # DATETIME DETECTION
    # =========================================================

    @staticmethod
    def _detect_datetime_columns(
        df: pd.DataFrame
    ) -> list[str]:

        detected = []

        for column in df.columns:

            series = df[column]

            if pd.api.types.is_datetime64_any_dtype(
                series
            ):

                detected.append(column)
                continue

            if (
                series.dtype == "object"
                or
                pd.api.types.is_string_dtype(
                    series
                )
            ):

                sample = (
                    series
                    .dropna()
                    .astype(str)
                    .head(100)
                )

                if sample.empty:
                    continue

                try:

                    parsed = pd.to_datetime(
                        sample,
                        errors="coerce",
                        format="mixed"
                    )

                    valid_ratio = (
                        parsed.notna().mean()
                    )

                    if valid_ratio >= 0.80:
                        detected.append(
                            column
                        )

                except Exception:
                    continue

        return detected

    # =========================================================
    # HEALTH SCORE
    # =========================================================

    @staticmethod
    def _health_score(
        df: pd.DataFrame
    ) -> dict[str, Any]:

        total_cells = (
            df.shape[0]
            * df.shape[1]
        )

        if total_cells == 0:

            return {
                "score": 0,
                "status": "Critical",
                "missing_pct": 100,
                "duplicate_pct": 0
            }

        missing_pct = (
            df.isna().sum().sum()
            / total_cells
            * 100
        )

        duplicate_pct = (
            df.duplicated().mean()
            * 100
            if len(df)
            else 0
        )

        score = 100

        score -= min(
            missing_pct * 0.70,
            50
        )

        score -= min(
            duplicate_pct * 0.30,
            20
        )

        score = max(
            0,
            min(
                100,
                score
            )
        )

        if score >= 90:
            status = "Excellent"

        elif score >= 75:
            status = "Healthy"

        elif score >= 60:
            status = "Needs Attention"

        elif score >= 40:
            status = "Poor"

        else:
            status = "Critical"

        return {

            "score":
                round(
                    float(score),
                    2
                ),

            "status":
                status,

            "missing_pct":
                round(
                    float(missing_pct),
                    2
                ),

            "duplicate_pct":
                round(
                    float(duplicate_pct),
                    2
                )
        }

    # =========================================================
    # CORRELATIONS
    # =========================================================

    @staticmethod
    def _correlations(
        df: pd.DataFrame,
        numeric_columns: list[str]
    ) -> pd.DataFrame:

        if len(numeric_columns) < 2:

            return pd.DataFrame(
                columns=[
                    "feature_a",
                    "feature_b",
                    "correlation",
                    "abs_correlation"
                ]
            )

        try:

            corr = (
                df[numeric_columns]
                .corr(
                    numeric_only=True
                )
            )

            records = []

            for i, first in enumerate(
                numeric_columns
            ):

                for second in numeric_columns[
                    i + 1:
                ]:

                    value = corr.loc[
                        first,
                        second
                    ]

                    if pd.isna(value):
                        continue

                    records.append({

                        "feature_a":
                            first,

                        "feature_b":
                            second,

                        "correlation":
                            round(
                                float(value),
                                4
                            ),

                        "abs_correlation":
                            round(
                                abs(
                                    float(value)
                                ),
                                4
                            )
                    })

            if not records:

                return pd.DataFrame(
                    columns=[
                        "feature_a",
                        "feature_b",
                        "correlation",
                        "abs_correlation"
                    ]
                )

            return (
                pd.DataFrame(records)
                .sort_values(
                    "abs_correlation",
                    ascending=False
                )
                .head(30)
                .reset_index(
                    drop=True
                )
            )

        except Exception:

            return pd.DataFrame()

    # =========================================================
    # OUTLIERS
    # =========================================================

    @staticmethod
    def _outliers(
        df: pd.DataFrame,
        numeric_columns: list[str]
    ) -> dict[str, Any]:

        results = {}

        total_outliers = 0

        for column in numeric_columns:

            series = pd.to_numeric(
                df[column],
                errors="coerce"
            ).dropna()

            if len(series) < 4:

                results[column] = {
                    "count": 0,
                    "percentage": 0,
                    "lower_bound": None,
                    "upper_bound": None
                }

                continue

            q1 = series.quantile(
                0.25
            )

            q3 = series.quantile(
                0.75
            )

            iqr = q3 - q1

            if iqr == 0:

                count = 0
                lower = q1
                upper = q3

            else:

                lower = (
                    q1 - 1.5 * iqr
                )

                upper = (
                    q3 + 1.5 * iqr
                )

                mask = (
                    (series < lower)
                    |
                    (series > upper)
                )

                count = int(
                    mask.sum()
                )

            total_outliers += count

            results[column] = {

                "count":
                    count,

                "percentage":
                    round(
                        count
                        / len(series)
                        * 100,
                        2
                    ),

                "lower_bound":
                    round(
                        float(lower),
                        4
                    ),

                "upper_bound":
                    round(
                        float(upper),
                        4
                    )
            }

        return {

            "total_outliers":
                total_outliers,

            "by_column":
                results
        }

    # =========================================================
    # DISTRIBUTIONS
    # =========================================================

    @staticmethod
    def _distributions(
        df: pd.DataFrame,
        numeric_columns: list[str]
    ) -> dict[str, Any]:

        distributions = {}

        for column in numeric_columns:

            series = pd.to_numeric(
                df[column],
                errors="coerce"
            ).dropna()

            if series.empty:
                continue

            skew = float(
                series.skew()
            )

            if skew > 1:
                shape = "Highly Right-Skewed"

            elif skew > 0.5:
                shape = "Right-Skewed"

            elif skew < -1:
                shape = "Highly Left-Skewed"

            elif skew < -0.5:
                shape = "Left-Skewed"

            else:
                shape = "Approximately Symmetric"

            distributions[column] = {

                "mean":
                    round(
                        float(series.mean()),
                        4
                    ),

                "median":
                    round(
                        float(series.median()),
                        4
                    ),

                "std":
                    round(
                        float(series.std()),
                        4
                    ),

                "min":
                    round(
                        float(series.min()),
                        4
                    ),

                "max":
                    round(
                        float(series.max()),
                        4
                    ),

                "skewness":
                    round(
                        skew,
                        4
                    ),

                "distribution":
                    shape
            }

        return distributions

    # =========================================================
    # TARGET ANALYSIS
    # =========================================================

    @staticmethod
    def _target_analysis(
        df: pd.DataFrame,
        target: str | None
    ) -> dict[str, Any]:

        if target is None:

            return {

                "available":
                    False,

                "target":
                    None,

                "reason":
                    "No target column detected."
            }

        if target not in df.columns:

            return {

                "available":
                    False,

                "target":
                    target
            }

        series = df[target]

        result = {

            "available":
                True,

            "target":
                target,

            "dtype":
                str(series.dtype),

            "missing":
                int(series.isna().sum()),

            "unique":
                int(
                    series.nunique(
                        dropna=True
                    )
                )
        }

        if pd.api.types.is_numeric_dtype(
            series
        ):

            numeric = pd.to_numeric(
                series,
                errors="coerce"
            ).dropna()

            if not numeric.empty:

                result.update({

                    "mean":
                        float(
                            numeric.mean()
                        ),

                    "median":
                        float(
                            numeric.median()
                        ),

                    "min":
                        float(
                            numeric.min()
                        ),

                    "max":
                        float(
                            numeric.max()
                        ),

                    "std":
                        float(
                            numeric.std()
                        )
                })

        else:

            value_counts = (
                series
                .value_counts(
                    dropna=True
                )
                .head(10)
            )

            result["top_values"] = (
                value_counts
                .to_dict()
            )

        return result

    # =========================================================
    # RISKS
    # =========================================================

    @staticmethod
    def _risks(
        df: pd.DataFrame,
        numeric_columns: list[str],
        categorical_columns: list[str]
    ) -> list[dict[str, Any]]:

        risks = []

        # Missing data.
        for column in df.columns:

            missing_pct = (
                df[column]
                .isna()
                .mean()
                * 100
            )

            if missing_pct >= 30:

                risks.append({

                    "type":
                        "Data Quality",

                    "severity":
                        "High",

                    "column":
                        column,

                    "message":
                        f"{missing_pct:.1f}% "
                        "of values are missing."
                })

            elif missing_pct >= 10:

                risks.append({

                    "type":
                        "Data Quality",

                    "severity":
                        "Medium",

                    "column":
                        column,

                    "message":
                        f"{missing_pct:.1f}% "
                        "of values are missing."
                })

        # Duplicate rows.
        duplicate_count = int(
            df.duplicated().sum()
        )

        if duplicate_count > 0:

            risks.append({

                "type":
                    "Data Quality",

                "severity":
                    "Medium",

                "column":
                    None,

                "message":
                    f"{duplicate_count:,} "
                    "duplicate rows detected."
            })

        # Numeric outlier risk.
        for column in numeric_columns:

            series = pd.to_numeric(
                df[column],
                errors="coerce"
            ).dropna()

            if len(series) < 4:
                continue

            q1 = series.quantile(
                0.25
            )

            q3 = series.quantile(
                0.75
            )

            iqr = q3 - q1

            if iqr <= 0:
                continue

            lower = (
                q1 - 1.5 * iqr
            )

            upper = (
                q3 + 1.5 * iqr
            )

            count = int(
                (
                    (series < lower)
                    |
                    (series > upper)
                ).sum()
            )

            percentage = (
                count
                / len(series)
                * 100
            )

            if percentage >= 10:

                risks.append({

                    "type":
                        "Outlier",

                    "severity":
                        "High",

                    "column":
                        column,

                    "message":
                        f"{percentage:.1f}% "
                        "of observations are "
                        "statistical outliers."
                })

            elif percentage >= 5:

                risks.append({

                    "type":
                        "Outlier",

                    "severity":
                        "Medium",

                    "column":
                        column,

                    "message":
                        f"{percentage:.1f}% "
                        "of observations are "
                        "statistical outliers."
                })

        # High-cardinality categorical fields.
        for column in categorical_columns:

            unique_count = (
                df[column]
                .nunique(
                    dropna=True
                )
            )

            if (
                len(df) > 0
                and
                unique_count
                / len(df)
                > 0.90
            ):

                risks.append({

                    "type":
                        "Cardinality",

                    "severity":
                        "Low",

                    "column":
                        column,

                    "message":
                        "Very high cardinality "
                        "categorical field."
                })

        # Sort by severity.
        priority = {

            "Critical": 0,
            "High": 1,
            "Medium": 2,
            "Low": 3
        }

        risks.sort(
            key=lambda item:
                priority.get(
                    item.get(
                        "severity"
                    ),
                    99
                )
        )

        return risks[:50]

    # =========================================================
    # KPI ENGINE
    # =========================================================

    @staticmethod
    def _kpis(
        df: pd.DataFrame,
        numeric_columns: list[str]
    ) -> dict[str, Any]:

        kpis = {}

        for column in numeric_columns:

            series = pd.to_numeric(
                df[column],
                errors="coerce"
            ).dropna()

            if series.empty:
                continue

            kpis[column] = {

                "sum":
                    round(
                        float(series.sum()),
                        2
                    ),

                "average":
                    round(
                        float(series.mean()),
                        2
                    ),

                "median":
                    round(
                        float(series.median()),
                        2
                    ),

                "min":
                    round(
                        float(series.min()),
                        2
                    ),

                "max":
                    round(
                        float(series.max()),
                        2
                    ),

                "growth_proxy_pct":
                    DecisionEngineHelper
                    .growth_proxy(
                        series
                    )
            }

        return kpis

    # =========================================================
    # ML READINESS
    # =========================================================

    @staticmethod
    def _ml_readiness(
        df: pd.DataFrame,
        target: str | None
    ) -> dict[str, Any]:

        rows = len(df)
        columns = len(df.columns)

        missing_pct = (
            df.isna()
            .mean()
            .mean()
            * 100
            if columns
            else 100
        )

        duplicate_pct = (
            df.duplicated().mean()
            * 100
            if rows
            else 0
        )

        score = 100

        score -= min(
            missing_pct,
            40
        )

        score -= min(
            duplicate_pct * 0.5,
            15
        )

        if rows < 100:
            score -= 20

        elif rows < 500:
            score -= 10

        if target is None:
            score -= 15

        score = max(
            0,
            min(
                100,
                score
            )
        )

        if score >= 80:
            status = "Ready"

        elif score >= 60:
            status = "Mostly Ready"

        elif score >= 40:
            status = "Needs Preparation"

        else:
            status = "Not Ready"

        return {

            "score":
                round(
                    float(score),
                    2
                ),

            "status":
                status,

            "rows":
                rows,

            "features":
                max(
                    columns - 1,
                    0
                ),

            "target":
                target,

            "missing_pct":
                round(
                    float(missing_pct),
                    2
                ),

            "duplicate_pct":
                round(
                    float(duplicate_pct),
                    2
                )
        }

    # =========================================================
    # EXECUTIVE SUMMARY
    # =========================================================

    @staticmethod
    def _executive_summary(
        data: pd.DataFrame,
        target: str | None,
        health: dict[str, Any],
        risks: list[dict[str, Any]],
        outliers: dict[str, Any],
        correlations: pd.DataFrame,
        target_analysis: dict[str, Any],
        ml_readiness: dict[str, Any]
    ) -> dict[str, Any]:

        high_risks = sum(

            1
            for risk in risks
            if risk.get("severity")
            in {"Critical", "High"}
        )

        summary = []

        summary.append(

            f"Dataset contains "
            f"{len(data):,} rows and "
            f"{len(data.columns):,} columns."
        )

        summary.append(

            f"Data health score is "
            f"{health.get('score', 0):.1f}/100 "
            f"({health.get('status', 'Unknown')})."
        )

        if target:

            summary.append(

                f"Primary analytical target: "
                f"{target}."
            )

        if high_risks:

            summary.append(

                f"{high_risks} high-priority "
                "risk(s) require attention."
            )

        else:

            summary.append(
                "No critical data risks "
                "were detected."
            )

        total_outliers = outliers.get(
            "total_outliers",
            0
        )

        if total_outliers:

            summary.append(

                f"{total_outliers:,} "
                "potential outlier observations "
                "were detected."
            )

        if not correlations.empty:

            strongest = correlations.iloc[0]

            summary.append(

                f"Strongest numeric relationship: "
                f"{strongest['feature_a']} ↔ "
                f"{strongest['feature_b']} "
                f"({strongest['correlation']:.2f})."
            )

        return {

            "headline":
                (
                    "NEXUS AI completed "
                    "an autonomous dataset "
                    "intelligence assessment."
                ),

            "summary":
                " ".join(summary),

            "high_priority_risks":
                high_risks,

            "target":
                target,

            "health_score":
                health.get(
                    "score",
                    0
                ),

            "ml_readiness":
                ml_readiness.get(
                    "status",
                    "Unknown"
                )
        }

    # =========================================================
    # RECOMMENDATIONS
    # =========================================================

    @staticmethod
    def _recommendations(
        data: pd.DataFrame,
        target: str | None,
        health: dict[str, Any],
        risks: list[dict[str, Any]],
        outliers: dict[str, Any],
        correlations: pd.DataFrame,
        target_analysis: dict[str, Any],
        ml_readiness: dict[str, Any]
    ) -> list[dict[str, Any]]:

        recommendations = []

        # Health recommendation.
        if health.get(
            "missing_pct",
            0
        ) > 10:

            recommendations.append({

                "priority":
                    "High",

                "category":
                    "Data Quality",

                "action":
                    "Investigate and treat "
                    "missing values before "
                    "advanced modeling."
            })

        # Duplicate recommendation.
        if health.get(
            "duplicate_pct",
            0
        ) > 2:

            recommendations.append({

                "priority":
                    "Medium",

                "category":
                    "Data Quality",

                "action":
                    "Review duplicate records "
                    "and establish a deduplication "
                    "rule."
            })

        # Outlier recommendation.
        if outliers.get(
            "total_outliers",
            0
        ) > 0:

            recommendations.append({

                "priority":
                    "Medium",

                "category":
                    "Anomaly Detection",

                "action":
                    "Investigate detected outliers "
                    "before using sensitive "
                    "statistical or ML models."
            })

        # Correlation recommendation.
        if not correlations.empty:

            strongest = correlations.iloc[0]

            if (
                abs(
                    float(
                        strongest[
                            "correlation"
                        ]
                    )
                )
                >= 0.80
            ):

                recommendations.append({

                    "priority":
                        "Medium",

                    "category":
                        "Feature Engineering",

                    "action":
                        (
                            f"Review the strong "
                            f"relationship between "
                            f"{strongest['feature_a']} "
                            f"and "
                            f"{strongest['feature_b']} "
                            "for multicollinearity "
                            "or business dependency."
                        )
                })

        # Target recommendation.
        if target is None:

            recommendations.append({

                "priority":
                    "Medium",

                "category":
                    "Machine Learning",

                "action":
                    "Select a business target "
                    "to activate predictive "
                    "modeling and driver analysis."
            })

        # ML readiness.
        if ml_readiness.get(
            "score",
            0
        ) < 60:

            recommendations.append({

                "priority":
                    "High",

                "category":
                    "ML Readiness",

                "action":
                    "Improve data quality, "
                    "sample size, and target "
                    "definition before training "
                    "production models."
            })

        if not recommendations:

            recommendations.append({

                "priority":
                    "Low",

                "category":
                    "Optimization",

                "action":
                    "Dataset is suitable for "
                    "deeper predictive analytics "
                    "and decision intelligence."
            })

        return recommendations


# =============================================================
# HELPER
# =============================================================

class DecisionEngineHelper:
    """
    Lightweight statistical helpers used by the orchestrator.
    """

    @staticmethod
    def growth_proxy(
        series: pd.Series
    ) -> float:

        values = pd.to_numeric(
            series,
            errors="coerce"
        ).dropna()

        if len(values) < 2:
            return 0.0

        first = float(
            values.iloc[0]
        )

        last = float(
            values.iloc[-1]
        )

        if first == 0:
            return 0.0

        return round(
            (
                last / first
                - 1
            )
            * 100,
            2
        )