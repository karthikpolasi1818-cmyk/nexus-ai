from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import numpy as np
import pandas as pd

from sklearn.ensemble import (
    IsolationForest,
    RandomForestRegressor,
    RandomForestClassifier,
)
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder


# ============================================================
# QUALITY RESULT
# ============================================================

@dataclass
class QualityResult:
    score: float
    rows: int
    columns: int

    missing_cells: int
    missing_percentage: float

    duplicate_rows: int
    duplicate_percentage: float

    constant_columns: list[str]
    high_cardinality_columns: list[str]

    numeric_columns: int
    categorical_columns: int
    datetime_columns: int

    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# ADVANCED INTELLIGENCE ENGINE
# ============================================================

class AdvancedIntelligence:

    VERSION = "5.0.0"

    # ========================================================
    # SAFE DATETIME PARSING
    # ========================================================

    @staticmethod
    def _safe_datetime_parse(
        series: pd.Series,
    ) -> pd.Series:

        if series.empty:
            return pd.Series(
                pd.NaT,
                index=series.index,
                dtype="datetime64[ns]",
            )

        try:
            return pd.to_datetime(
                series,
                errors="coerce",
                format="mixed",
            )

        except Exception:

            try:
                return pd.to_datetime(
                    series,
                    errors="coerce",
                )

            except Exception:

                return pd.Series(
                    pd.NaT,
                    index=series.index,
                    dtype="datetime64[ns]",
                )

    # ========================================================
    # COLUMN ROLE DETECTION
    # ========================================================

    @staticmethod
    def _infer_role(
        series: pd.Series,
    ) -> str:

        name = str(
            series.name
        ).strip().lower()

        # ----------------------------------------------------
        # EMPTY
        # ----------------------------------------------------

        if series.dropna().empty:
            return "empty"

        # ----------------------------------------------------
        # DATETIME
        # ----------------------------------------------------

        if pd.api.types.is_datetime64_any_dtype(
            series
        ):
            return "date"

        # ----------------------------------------------------
        # BOOLEAN
        # ----------------------------------------------------

        if pd.api.types.is_bool_dtype(
            series
        ):
            return "boolean"

        # ----------------------------------------------------
        # IDENTIFIERS
        # ----------------------------------------------------

        identifier_keywords = [
            "id",
            "code",
            "zip",
            "zipcode",
            "pincode",
            "pin_code",
            "phone",
            "mobile",
            "account",
            "customer_id",
            "product_id",
            "order_id",
            "transaction_id",
        ]

        # Exact ID-like names should not be treated as metrics.
        if (
            name in identifier_keywords
            or name.endswith("_id")
            or name.endswith(" id")
        ):
            return "identifier"

        # ----------------------------------------------------
        # NUMERIC
        # ----------------------------------------------------

        if pd.api.types.is_numeric_dtype(
            series
        ):
            return "numeric"

        # ----------------------------------------------------
        # DATE DETECTION
        # ----------------------------------------------------

        non_null = series.dropna()

        if len(non_null) >= 3:

            parsed = (
                AdvancedIntelligence
                ._safe_datetime_parse(
                    non_null
                )
            )

            parse_ratio = float(
                parsed.notna().mean()
            )

            date_keywords = [
                "date",
                "time",
                "timestamp",
                "datetime",
                "year",
                "month",
                "day",
            ]

            has_date_name = any(
                keyword in name
                for keyword in date_keywords
            )

            if (
                parse_ratio >= 0.90
                and has_date_name
            ):
                return "date"

            if (
                parse_ratio >= 0.98
                and len(non_null) >= 10
            ):
                return "date"

        # ----------------------------------------------------
        # CATEGORICAL
        # ----------------------------------------------------

        unique_count = int(
            series.nunique(
                dropna=True
            )
        )

        categorical_limit = max(
            20,
            int(
                len(series) * 0.05
            ),
        )

        if unique_count <= categorical_limit:
            return "categorical"

        # ----------------------------------------------------
        # TEXT
        # ----------------------------------------------------

        return "text"

    # ========================================================
    # SCHEMA INTELLIGENCE
    # ========================================================

    @staticmethod
    def schema(
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        rows = []

        total = max(
            len(df),
            1,
        )

        for column in df.columns:

            series = df[column]

            try:
                unique_count = int(
                    series.nunique(
                        dropna=True
                    )
                )
            except Exception:
                unique_count = 0

            missing_count = int(
                series.isna().sum()
            )

            rows.append(
                {
                    "column": str(column),

                    "dtype":
                        str(series.dtype),

                    "role":
                        AdvancedIntelligence
                        ._infer_role(series),

                    "missing":
                        missing_count,

                    "missing_pct":
                        round(
                            missing_count
                            / total
                            * 100,
                            2,
                        ),

                    "unique":
                        unique_count,

                    "unique_pct":
                        round(
                            unique_count
                            / total
                            * 100,
                            2,
                        ),

                    "constant":
                        (
                            series.nunique(
                                dropna=False
                            )
                            <= 1
                        ),

                    "sample":
                        ", ".join(
                            map(
                                str,
                                series
                                .dropna()
                                .head(3)
                                .tolist(),
                            )
                        ),
                }
            )

        return pd.DataFrame(rows)

    # ========================================================
    # DATA QUALITY
    # ========================================================

    @staticmethod
    def quality_report(
        df: pd.DataFrame,
    ) -> QualityResult:

        rows, columns = df.shape

        total_cells = max(
            rows * max(columns, 1),
            1,
        )

        missing = int(
            df.isna()
            .sum()
            .sum()
        )

        duplicates = int(
            df.duplicated()
            .sum()
        )

        numeric_columns = len(
            df.select_dtypes(
                include="number"
            ).columns
        )

        categorical_columns = len(
    df.select_dtypes(
        include=[
            "str",
            "category",
        ]
    ).columns
)

        datetime_columns = len(
            df.select_dtypes(
                include=[
                    "datetime",
                    "datetimetz",
                ]
            ).columns
        )

        # ----------------------------------------------------
        # CONSTANT COLUMNS
        # ----------------------------------------------------

        constant = []

        for column in df.columns:

            try:

                if (
                    df[column]
                    .nunique(
                        dropna=False
                    )
                    <= 1
                ):
                    constant.append(
                        str(column)
                    )

            except Exception:
                continue

        # ----------------------------------------------------
        # HIGH CARDINALITY
        # ----------------------------------------------------

        high_cardinality = []

        for column in df.columns:

            try:

                unique_count = int(
                    df[column]
                    .nunique(
                        dropna=True
                    )
                )

                if (
                    unique_count
                    > max(
                        100,
                        int(
                            len(df) * 0.5
                        ),
                    )
                ):
                    high_cardinality.append(
                        str(column)
                    )

            except Exception:
                continue

        warnings = []

        missing_percentage = (
            missing
            / total_cells
            * 100
        )

        duplicate_percentage = (
            duplicates
            / max(rows, 1)
            * 100
        )

        # ----------------------------------------------------
        # WARNINGS
        # ----------------------------------------------------

        if missing_percentage > 30:
            warnings.append(
                "Critical missing-value exposure."
            )

        elif missing_percentage > 20:
            warnings.append(
                "High missing-value exposure."
            )

        elif missing_percentage > 10:
            warnings.append(
                "Moderate missing-value exposure."
            )

        if duplicates > 0:
            warnings.append(
                f"{duplicates:,} duplicate rows detected."
            )

        if constant:
            warnings.append(
                f"{len(constant)} constant column(s) detected."
            )

        if high_cardinality:
            warnings.append(
                "High-cardinality columns detected: "
                + ", ".join(
                    high_cardinality[:5]
                )
            )

        if rows < 30:
            warnings.append(
                "Small dataset: statistical and ML "
                "conclusions may have low confidence."
            )

        if columns > 100:
            warnings.append(
                "High-dimensional dataset detected."
            )

        # ----------------------------------------------------
        # QUALITY SCORE
        # ----------------------------------------------------

        score = 100.0

        score -= min(
            35.0,
            missing_percentage * 0.75,
        )

        score -= min(
            20.0,
            duplicate_percentage * 0.50,
        )

        score -= min(
            10.0,
            len(constant) * 2.0,
        )

        score -= min(
            10.0,
            len(high_cardinality) * 2.0,
        )

        if rows < 30:
            score -= 5

        score = round(
            max(
                score,
                0.0,
            ),
            1,
        )

        return QualityResult(
            score=score,
            rows=rows,
            columns=columns,
            missing_cells=missing,
            missing_percentage=round(
                missing_percentage,
                2,
            ),
            duplicate_rows=duplicates,
            duplicate_percentage=round(
                duplicate_percentage,
                2,
            ),
            constant_columns=constant,
            high_cardinality_columns=high_cardinality,
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            datetime_columns=datetime_columns,
            warnings=warnings,
        )

    # ========================================================
    # HEALTH SCORE
    # ========================================================

    @staticmethod
    def health_score(
        df: pd.DataFrame,
    ) -> dict[str, Any]:

        quality = (
            AdvancedIntelligence
            .quality_report(df)
        )

        score = quality.score

        if score >= 90:
            status = "EXCELLENT"

        elif score >= 75:
            status = "GOOD"

        elif score >= 60:
            status = "FAIR"

        elif score >= 40:
            status = "POOR"

        else:
            status = "CRITICAL"

        return {
            "score": score,
            "status": status,
            "rows": quality.rows,
            "columns": quality.columns,
            "missing_percentage":
                quality.missing_percentage,
            "duplicate_percentage":
                quality.duplicate_percentage,
            "warnings":
                quality.warnings,
        }

    # ========================================================
    # METADATA
    # ========================================================

    @staticmethod
    def metadata(
        df: pd.DataFrame,
    ) -> dict[str, Any]:

        memory_mb = (
            df.memory_usage(
                deep=True
            ).sum()
            / 1024
            / 1024
        )

        return {
            "engine_version":
                AdvancedIntelligence.VERSION,

            "rows":
                int(len(df)),

            "columns":
                int(len(df.columns)),

            "memory_mb":
                round(
                    float(memory_mb),
                    3,
                ),

            "total_cells":
                int(
                    df.shape[0]
                    * df.shape[1]
                ),

            "numeric_columns":
                df.select_dtypes(
                    include="number"
                )
                .columns
                .tolist(),

            "categorical_columns":
                df.select_dtypes(
                    include=[
                        "str",
                        "category",
                    ]
                )
                .columns
                .tolist(),

            "datetime_columns":
                df.select_dtypes(
                    include=[
                        "datetime",
                        "datetimetz",
                    ]
                )
                .columns
                .tolist(),
        }

    # ========================================================
    # ANOMALY ENSEMBLE
    # ========================================================

    @staticmethod
    def anomaly_ensemble(
        df: pd.DataFrame,
        column: str,
        contamination: float = 0.03,
    ) -> pd.DataFrame:

        if column not in df.columns:
            raise ValueError(
                f"Column '{column}' not found."
            )

        result = df.copy()

        values = pd.to_numeric(
            result[column],
            errors="coerce",
        )

        valid = values.notna()

        result["anomaly_score"] = np.nan
        result["anomaly"] = False
        result["anomaly_reason"] = "Normal"

        x = values.loc[
            valid
        ].to_numpy(
            dtype=float
        )

        if (
            len(x) < 12
            or np.nanstd(x) == 0
        ):
            return result

        # ----------------------------------------------------
        # ROBUST Z-SCORE
        # ----------------------------------------------------

        median = np.median(x)

        mad = np.median(
            np.abs(
                x - median
            )
        )

        robust_z = np.abs(
            (
                x - median
            )
            /
            (
                1.4826 * mad
                + 1e-9
            )
        )

        # ----------------------------------------------------
        # ISOLATION FOREST
        # ----------------------------------------------------

        contamination = min(
            max(
                float(contamination),
                0.001,
            ),
            0.20,
        )

        model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=300,
            n_jobs=-1,
        )

        model.fit(
            x.reshape(-1, 1)
        )

        isolation_raw = (
            -model.score_samples(
                x.reshape(-1, 1)
            )
        )

        isolation_flags = (
            model.predict(
                x.reshape(-1, 1)
            )
            == -1
        )

        robust_flags = (
            robust_z >= 3.5
        )

        # ----------------------------------------------------
        # NORMALIZATION
        # ----------------------------------------------------

        def normalize(
            array: np.ndarray,
        ) -> np.ndarray:

            low = np.nanpercentile(
                array,
                5,
            )

            high = np.nanpercentile(
                array,
                95,
            )

            if np.isclose(
                low,
                high,
            ):
                return np.zeros_like(
                    array,
                    dtype=float,
                )

            return np.clip(
                (
                    array - low
                )
                /
                (
                    high - low
                ),
                0,
                1,
            )

        robust_score = normalize(
            robust_z
        )

        isolation_score = normalize(
            isolation_raw
        )

        # ----------------------------------------------------
        # ENSEMBLE
        # ----------------------------------------------------

        combined_score = (
            0.60 * robust_score
            +
            0.40 * isolation_score
        )

        flags = (
            robust_flags
            | isolation_flags
        )

        reasons = np.full(
            len(x),
            "Normal",
            dtype=object,
        )

        reasons[
            isolation_flags
            & ~robust_flags
        ] = "Isolation Forest"

        reasons[
            robust_flags
            & ~isolation_flags
        ] = "Robust Z-score"

        reasons[
            robust_flags
            & isolation_flags
        ] = (
            "Robust Z-score + Isolation Forest"
        )

        indexes = result.index[
            valid
        ]

        result.loc[
            indexes,
            "anomaly_score",
        ] = np.round(
            combined_score,
            4,
        )

        result.loc[
            indexes,
            "anomaly",
        ] = flags

        result.loc[
            indexes,
            "anomaly_reason",
        ] = reasons

        return (
            result
            .sort_values(
                "anomaly_score",
                ascending=False,
            )
        )

    # ========================================================
    # DISTRIBUTION INTELLIGENCE
    # ========================================================

    @staticmethod
    def distributions(
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        rows = []

        numeric_columns = (
            df.select_dtypes(
                include="number"
            )
            .columns
            .tolist()
        )

        for column in numeric_columns:

            series = pd.to_numeric(
                df[column],
                errors="coerce",
            ).dropna()

            if series.empty:
                continue

            rows.append(
                {
                    "column": column,
                    "count":
                        int(series.count()),
                    "mean":
                        round(
                            float(
                                series.mean()
                            ),
                            4,
                        ),
                    "median":
                        round(
                            float(
                                series.median()
                            ),
                            4,
                        ),
                    "std":
                        round(
                            float(
                                series.std()
                            ),
                            4,
                        ),
                    "min":
                        round(
                            float(
                                series.min()
                            ),
                            4,
                        ),
                    "max":
                        round(
                            float(
                                series.max()
                            ),
                            4,
                        ),
                    "q25":
                        round(
                            float(
                                series.quantile(
                                    0.25
                                )
                            ),
                            4,
                        ),
                    "q75":
                        round(
                            float(
                                series.quantile(
                                    0.75
                                )
                            ),
                            4,
                        ),
                    "iqr":
                        round(
                            float(
                                series.quantile(
                                    0.75
                                )
                                -
                                series.quantile(
                                    0.25
                                )
                            ),
                            4,
                        ),
                    "skewness":
                        round(
                            float(
                                series.skew()
                            ),
                            4,
                        ),
                    "kurtosis":
                        round(
                            float(
                                series.kurtosis()
                            ),
                            4,
                        ),
                    "zeros":
                        int(
                            (series == 0).sum()
                        ),
                    "negative_values":
                        int(
                            (series < 0).sum()
                        ),
                    "positive_values":
                        int(
                            (series > 0).sum()
                        ),
                }
            )

        return pd.DataFrame(rows)

    # ========================================================
    # NUMERIC SUMMARY
    # ========================================================

    @staticmethod
    def numeric_summary(
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        numeric = df.select_dtypes(
            include="number"
        )

        if numeric.empty:
            return pd.DataFrame()

        return (
            numeric
            .describe()
            .T
            .reset_index()
            .rename(
                columns={
                    "index": "feature"
                }
            )
        )

    # ========================================================
    # CATEGORICAL SUMMARY
    # ========================================================

    @staticmethod
    def categorical_summary(
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        categorical = df.select_dtypes(
            include=[
                "str",
                "category",
                "bool",
            ]
        )

        rows = []

        for column in categorical.columns:

            series = (
                categorical[column]
                .dropna()
            )

            if series.empty:
                continue

            mode = series.mode()

            top_value = (
                mode.iloc[0]
                if not mode.empty
                else None
            )

            top_count = int(
                (
                    series
                    == top_value
                ).sum()
            )

            rows.append(
                {
                    "column": column,

                    "unique":
                        int(
                            series.nunique()
                        ),

                    "top":
                        str(top_value),

                    "top_count":
                        top_count,

                    "top_percentage":
                        round(
                            top_count
                            / len(series)
                            * 100,
                            2,
                        ),
                }
            )

        return pd.DataFrame(rows)

    # ========================================================
    # TARGET ANALYSIS
    # ========================================================

    @staticmethod
    def target_analysis(
        df: pd.DataFrame,
        target: str | None,
    ) -> dict[str, Any]:

        if (
            not target
            or target not in df.columns
        ):
            return {
                "target": target,
                "available": False,
            }

        numeric = pd.to_numeric(
            df[target],
            errors="coerce",
        )

        valid = numeric.dropna()

        if valid.empty:
            return {
                "target": target,
                "available": False,
                "reason":
                    "Target is not numeric.",
            }

        mean = float(
            valid.mean()
        )

        std = float(
            valid.std()
        )

        median = float(
            valid.median()
        )

        minimum = float(
            valid.min()
        )

        maximum = float(
            valid.max()
        )

        return {
            "target": target,
            "available": True,
            "count":
                int(len(valid)),
            "mean": mean,
            "median": median,
            "min": minimum,
            "max": maximum,
            "std": std,
            "sum":
                float(valid.sum()),
            "range":
                maximum - minimum,
            "variance":
                float(valid.var()),
            "coefficient_of_variation":
                float(
                    std
                    /
                    (
                        abs(mean)
                        + 1e-9
                    )
                ),
            "missing":
                int(
                    numeric.isna().sum()
                ),
            "missing_percentage":
                round(
                    float(
                        numeric.isna()
                        .mean()
                        * 100
                    ),
                    2,
                ),
        }

    # ========================================================
    # TARGET CANDIDATES
    # ========================================================

    @staticmethod
    def target_candidates(
        df: pd.DataFrame,
    ) -> list[str]:

        candidates = []

        numeric = (
            df.select_dtypes(
                include="number"
            ).columns
        )

        keywords = [
            "sales",
            "revenue",
            "profit",
            "amount",
            "income",
            "price",
            "value",
            "target",
            "score",
            "quantity",
        ]

        for column in numeric:

            name = str(
                column
            ).lower()

            score = sum(
                keyword in name
                for keyword in keywords
            )

            if score > 0:
                candidates.append(
                    (
                        score,
                        column,
                    )
                )

        candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            column
            for _, column
            in candidates
        ]

    # ========================================================
    # DATETIME CANDIDATES
    # ========================================================

    @staticmethod
    def datetime_candidates(
        df: pd.DataFrame,
    ) -> list[str]:

        candidates = []

        for column in df.columns:

            if (
                AdvancedIntelligence
                ._infer_role(
                    df[column]
                )
                == "date"
            ):
                candidates.append(
                    column
                )

        return candidates

    # ========================================================
    # FEATURE IMPORTANCE
    # ========================================================

    @staticmethod
    def feature_importance(
        df: pd.DataFrame,
        target: str,
        top_n: int = 15,
    ) -> pd.DataFrame:

        empty = pd.DataFrame(
            columns=[
                "feature",
                "importance",
                "std",
            ]
        )

        if target not in df.columns:
            return empty

        work = df.copy()

        # ----------------------------------------------------
        # TARGET
        # ----------------------------------------------------

        y_numeric = pd.to_numeric(
            work[target],
            errors="coerce",
        )

        numeric_ratio = float(
            y_numeric.notna().mean()
        )

        if numeric_ratio >= 0.80:

            valid = y_numeric.notna()

            work = work.loc[
                valid
            ].copy()

            y = y_numeric.loc[
                valid
            ]

            task_type = "regression"

        else:

            target_series = (
                work[target]
                .astype(str)
                .fillna("UNKNOWN")
            )

            y = (
                target_series
                .astype("category")
                .cat.codes
            )

            work = work.loc[
                y.index
            ].copy()

            task_type = "classification"

        if len(work) < 30:
            return empty

        X = work.drop(
            columns=[target]
        )

        # ----------------------------------------------------
        # REMOVE EMPTY COLUMNS
        # ----------------------------------------------------

        X = X.drop(
            columns=[
                column
                for column in X.columns
                if X[column].isna().all()
            ],
            errors="ignore",
        )

        if X.empty:
            return empty

        # ----------------------------------------------------
        # DATETIME FEATURES
        # ----------------------------------------------------

        datetime_columns = []

        for column in X.columns:

            if (
                AdvancedIntelligence
                ._infer_role(
                    X[column]
                )
                == "date"
            ):
                datetime_columns.append(
                    column
                )

        for column in datetime_columns:

            parsed = (
                AdvancedIntelligence
                ._safe_datetime_parse(
                    X[column]
                )
            )

            X[
                f"{column}__year"
            ] = parsed.dt.year

            X[
                f"{column}__month"
            ] = parsed.dt.month

            X[
                f"{column}__day"
            ] = parsed.dt.day

            X[
                f"{column}__dayofweek"
            ] = parsed.dt.dayofweek

            X = X.drop(
                columns=[column]
            )

        # ----------------------------------------------------
        # CATEGORICAL ENCODING
        # ----------------------------------------------------

        categorical = (
            X.select_dtypes(
                exclude="number"
            )
            .columns
            .tolist()
        )

        if categorical:

            encoder = OrdinalEncoder(
                handle_unknown=
                "use_encoded_value",
                unknown_value=-1,
            )

            encoded = (
                X[categorical]
                .astype(str)
                .fillna("MISSING")
            )

            try:

                X[categorical] = (
                    encoder
                    .fit_transform(
                        encoded
                    )
                )

            except Exception:

                for column in categorical:
                    X[column] = (
                        X[column]
                        .astype("category")
                        .cat.codes
                    )

        # ----------------------------------------------------
        # NUMERIC CLEANING
        # ----------------------------------------------------

        X = X.apply(
            pd.to_numeric,
            errors="coerce",
        )

        X = X.replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )

        X = X.fillna(0)

        X = X.loc[
            :,
            X.nunique() > 1,
        ]

        if X.empty:
            return empty

        # ----------------------------------------------------
        # TRAIN / TEST
        # ----------------------------------------------------

        try:

            stratify = None

            if task_type == "classification":

                value_counts = (
                    pd.Series(y)
                    .value_counts()
                )

                if (
                    len(value_counts) > 1
                    and value_counts.min() >= 2
                ):
                    stratify = y

            (
                X_train,
                X_test,
                y_train,
                y_test,
            ) = train_test_split(
                X,
                y,
                test_size=0.20,
                random_state=42,
                stratify=stratify,
            )

        except Exception:
            return empty

        # ----------------------------------------------------
        # MODEL
        # ----------------------------------------------------

        try:

            if task_type == "regression":

                model = RandomForestRegressor(
                    n_estimators=300,
                    random_state=42,
                    n_jobs=-1,
                    max_features="sqrt",
                )

            else:

                model = RandomForestClassifier(
                    n_estimators=300,
                    random_state=42,
                    n_jobs=-1,
                    max_features="sqrt",
                )

            model.fit(
                X_train,
                y_train,
            )

        except Exception:
            return empty

        # ----------------------------------------------------
        # PERMUTATION IMPORTANCE
        # ----------------------------------------------------

        try:

            importance = (
                permutation_importance(
                    model,
                    X_test,
                    y_test,
                    n_repeats=8,
                    random_state=42,
                    n_jobs=-1,
                )
            )

            result = pd.DataFrame(
                {
                    "feature":
                        X.columns,

                    "importance":
                        importance
                        .importances_mean,

                    "std":
                        importance
                        .importances_std,
                }
            )

        except Exception:

            result = pd.DataFrame(
                {
                    "feature":
                        X.columns,

                    "importance":
                        model
                        .feature_importances_,

                    "std":
                        0.0,
                }
            )

        return (
            result
            .sort_values(
                "importance",
                ascending=False,
            )
            .head(top_n)
            .reset_index(
                drop=True
            )
        )

    # ========================================================
    # AUTOMATIC DATASET SUMMARY
    # ========================================================

    @staticmethod
    def executive_summary(
        df: pd.DataFrame,
    ) -> dict[str, Any]:

        quality = (
            AdvancedIntelligence
            .quality_report(df)
        )

        numeric = (
            df.select_dtypes(
                include="number"
            )
        )

        summary = {
            "dataset_size":
                f"{len(df):,} rows × "
                f"{len(df.columns):,} columns",

            "health_score":
                quality.score,

            "health_status":
                (
                    "EXCELLENT"
                    if quality.score >= 90
                    else "GOOD"
                    if quality.score >= 75
                    else "FAIR"
                    if quality.score >= 60
                    else "POOR"
                    if quality.score >= 40
                    else "CRITICAL"
                ),

            "missing_cells":
                quality.missing_cells,

            "duplicate_rows":
                quality.duplicate_rows,

            "numeric_features":
                len(numeric.columns),

            "warnings":
                quality.warnings,
        }

        # ----------------------------------------------------
        # TOP NUMERIC SIGNALS
        # ----------------------------------------------------

        if not numeric.empty:

            variability = (
                numeric.std(
                    numeric_only=True
                )
                .sort_values(
                    ascending=False
                )
                .head(5)
            )

            summary[
                "high_variability_features"
            ] = variability.index.tolist()

        else:

            summary[
                "high_variability_features"
            ] = []

        return summary

    # ========================================================
    # NUMERIC OUTLIER SUMMARY
    # ========================================================

    @staticmethod
    def outlier_summary(
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        rows = []

        numeric_columns = (
            df.select_dtypes(
                include="number"
            ).columns
        )

        for column in numeric_columns:

            values = pd.to_numeric(
                df[column],
                errors="coerce",
            ).dropna()

            if len(values) < 4:
                continue

            q1 = float(
                values.quantile(0.25)
            )

            q3 = float(
                values.quantile(0.75)
            )

            iqr = q3 - q1

            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            count = int(
                (
                    (values < lower)
                    |
                    (values > upper)
                ).sum()
            )

            rows.append(
                {
                    "column":
                        column,

                    "outlier_count":
                        count,

                    "outlier_percentage":
                        round(
                            count
                            / len(values)
                            * 100,
                            2,
                        ),

                    "lower_bound":
                        lower,

                    "upper_bound":
                        upper,
                }
            )

        return pd.DataFrame(rows)
