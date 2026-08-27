from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import (
    LinearRegression,
    LogisticRegression,
)
from sklearn.ensemble import (
    RandomForestRegressor,
    RandomForestClassifier,
    GradientBoostingRegressor,
    GradientBoostingClassifier,
)
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
)


class PredictiveIntelligence:
    """
    NEXUS AI Predictive Intelligence Engine.

    Automatically:
    - Detects regression/classification
    - Prepares features
    - Trains multiple models
    - Compares models
    - Selects the best model
    - Calculates feature importance
    - Generates predictions
    """

    VERSION = "1.0.0"

    # =========================================================
    # PUBLIC API
    # =========================================================

    @classmethod
    def analyze(
        cls,
        df: pd.DataFrame,
        target: str,
        test_size: float = 0.20,
        random_state: int = 42,
    ) -> dict[str, Any]:

        if df is None or df.empty:
            raise ValueError(
                "Predictive Intelligence received an empty dataset."
            )

        if target not in df.columns:
            raise ValueError(
                f"Target column '{target}' was not found."
            )

        if len(df) < 20:
            raise ValueError(
                "At least 20 rows are recommended for predictive modeling."
            )

        data = df.copy()

        data = data.dropna(
            axis=0,
            how="all"
        )

        if target not in data.columns:
            raise ValueError(
                f"Target column '{target}' is unavailable."
            )

        # Remove rows where target is missing.
        data = data.dropna(
            subset=[target]
        )

        if len(data) < 20:
            raise ValueError(
                "Not enough valid target observations."
            )

        X = data.drop(
            columns=[target]
        )

        y = data[target]

        # Remove completely empty columns.
        X = X.dropna(
            axis=1,
            how="all"
        )

        if X.shape[1] == 0:
            raise ValueError(
                "No usable feature columns were detected."
            )

        problem_type = cls.detect_problem_type(
            y
        )

        numeric_features = (
            X.select_dtypes(
                include=np.number
            )
            .columns
            .tolist()
        )

        categorical_features = (
            X.select_dtypes(
                exclude=np.number
            )
            .columns
            .tolist()
        )

        if problem_type == "regression":

            models = cls._regression_models()

        else:

            models = cls._classification_models()

        preprocessor = cls._preprocessor(
            numeric_features,
            categorical_features
        )

        stratify = None

        if problem_type == "classification":

            counts = y.value_counts()

            if (
                len(counts) > 1
                and counts.min() >= 2
            ):
                stratify = y

        try:

            X_train, X_test, y_train, y_test = (
                train_test_split(
                    X,
                    y,
                    test_size=test_size,
                    random_state=random_state,
                    stratify=stratify,
                )
            )

        except ValueError:

            X_train, X_test, y_train, y_test = (
                train_test_split(
                    X,
                    y,
                    test_size=test_size,
                    random_state=random_state,
                )
            )

        model_results = []

        trained_models = {}

        for model_name, model in models.items():

            try:

                pipeline = Pipeline(
                    steps=[
                        (
                            "preprocessor",
                            preprocessor
                        ),
                        (
                            "model",
                            model
                        ),
                    ]
                )

                pipeline.fit(
                    X_train,
                    y_train
                )

                predictions = pipeline.predict(
                    X_test
                )

                metrics = cls._evaluate(
                    problem_type,
                    y_test,
                    predictions
                )

                model_results.append({

                    "model":
                        model_name,

                    **metrics,

                    "status":
                        "Success"
                })

                trained_models[
                    model_name
                ] = pipeline

            except Exception as error:

                model_results.append({

                    "model":
                        model_name,

                    "status":
                        "Failed",

                    "error":
                        str(error)
                })

        results_df = pd.DataFrame(
            model_results
        )

        successful = results_df[
            results_df["status"] == "Success"
        ].copy()

        if successful.empty:

            raise RuntimeError(
                "All predictive models failed."
            )

        if problem_type == "regression":

            successful = successful.sort_values(
                "r2",
                ascending=False
            )

        else:

            successful = successful.sort_values(
                "f1",
                ascending=False
            )

        best_model_name = (
            successful.iloc[0]["model"]
        )

        best_model = trained_models[
            best_model_name
        ]

        feature_importance = (
            cls._feature_importance(
                best_model,
                numeric_features,
                categorical_features
            )
        )

        test_predictions = best_model.predict(
            X_test
        )

        prediction_table = X_test.copy()

        prediction_table[
            "actual"
        ] = y_test.values

        prediction_table[
            "prediction"
        ] = test_predictions

        if problem_type == "classification":

            try:

                probabilities = (
                    best_model.predict_proba(
                        X_test
                    )
                )

                if probabilities.shape[1] == 2:

                    prediction_table[
                        "prediction_probability"
                    ] = probabilities[:, 1]

            except Exception:
                pass

        return {

            "version":
                cls.VERSION,

            "status":
                "success",

            "problem_type":
                problem_type,

            "target":
                target,

            "rows":
                int(len(data)),

            "features":
                int(X.shape[1]),

            "numeric_features":
                numeric_features,

            "categorical_features":
                categorical_features,

            "models_tested":
                list(models.keys()),

            "model_results":
                results_df,

            "best_model":
                best_model_name,

            "feature_importance":
                feature_importance,

            "predictions":
                prediction_table,

            "summary":
                cls._summary(
                    problem_type,
                    target,
                    best_model_name,
                    successful,
                    feature_importance
                )
        }

    # =========================================================
    # PROBLEM TYPE
    # =========================================================

    @staticmethod
    def detect_problem_type(
        y: pd.Series
    ) -> str:

        if not pd.api.types.is_numeric_dtype(y):
            return "classification"

        unique = y.nunique(
            dropna=True
        )

        # Numeric values with very few classes
        # are generally classification targets.
        if unique <= 10:
            return "classification"

        return "regression"

    # =========================================================
    # PREPROCESSOR
    # =========================================================

    @staticmethod
    def _preprocessor(
        numeric_features: list[str],
        categorical_features: list[str],
    ) -> ColumnTransformer:

        numeric_pipeline = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(
                        strategy="median"
                    )
                ),
                (
                    "scaler",
                    StandardScaler()
                ),
            ]
        )

        categorical_pipeline = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(
                        strategy="most_frequent"
                    )
                ),
                (
                    "encoder",
                    OneHotEncoder(
                        handle_unknown="ignore"
                    )
                ),
            ]
        )

        return ColumnTransformer(
            transformers=[

                (
                    "numeric",
                    numeric_pipeline,
                    numeric_features
                ),

                (
                    "categorical",
                    categorical_pipeline,
                    categorical_features
                )
            ],
            remainder="drop"
        )

    # =========================================================
    # REGRESSION MODELS
    # =========================================================

    @staticmethod
    def _regression_models():

        return {

            "Linear Regression":
                LinearRegression(),

            "Random Forest":
                RandomForestRegressor(
                    n_estimators=250,
                    max_depth=None,
                    min_samples_split=2,
                    random_state=42,
                    n_jobs=-1
                ),

            "Gradient Boosting":
                GradientBoostingRegressor(
                    n_estimators=200,
                    learning_rate=0.05,
                    max_depth=3,
                    random_state=42
                )
        }

    # =========================================================
    # CLASSIFICATION MODELS
    # =========================================================

    @staticmethod
    def _classification_models():

        return {

            "Logistic Regression":
                LogisticRegression(
                    max_iter=2000
                ),

            "Random Forest":
                RandomForestClassifier(
                    n_estimators=250,
                    random_state=42,
                    n_jobs=-1
                ),

            "Gradient Boosting":
                GradientBoostingClassifier(
                    n_estimators=200,
                    learning_rate=0.05,
                    max_depth=3,
                    random_state=42
                )
        }

    # =========================================================
    # EVALUATION
    # =========================================================

    @staticmethod
    def _evaluate(
        problem_type: str,
        actual: pd.Series,
        predictions
    ) -> dict[str, float]:

        if problem_type == "regression":

            mae = mean_absolute_error(
                actual,
                predictions
            )

            rmse = np.sqrt(
                mean_squared_error(
                    actual,
                    predictions
                )
            )

            r2 = r2_score(
                actual,
                predictions
            )

            return {

                "mae":
                    round(
                        float(mae),
                        4
                    ),

                "rmse":
                    round(
                        float(rmse),
                        4
                    ),

                "r2":
                    round(
                        float(r2),
                        4
                    )
            }

        accuracy = accuracy_score(
            actual,
            predictions
        )

        precision = precision_score(
            actual,
            predictions,
            average="weighted",
            zero_division=0
        )

        recall = recall_score(
            actual,
            predictions,
            average="weighted",
            zero_division=0
        )

        f1 = f1_score(
            actual,
            predictions,
            average="weighted",
            zero_division=0
        )

        return {

            "accuracy":
                round(
                    float(accuracy),
                    4
                ),

            "precision":
                round(
                    float(precision),
                    4
                ),

            "recall":
                round(
                    float(recall),
                    4
                ),

            "f1":
                round(
                    float(f1),
                    4
                )
        }

    # =========================================================
    # FEATURE IMPORTANCE
    # =========================================================

    @staticmethod
    def _feature_importance(
        pipeline: Pipeline,
        numeric_features: list[str],
        categorical_features: list[str]
    ) -> pd.DataFrame:

        try:

            preprocessor = (
                pipeline.named_steps[
                    "preprocessor"
                ]
            )

            model = (
                pipeline.named_steps[
                    "model"
                ]
            )

            feature_names = (
                preprocessor
                .get_feature_names_out()
            )

            if hasattr(
                model,
                "feature_importances_"
            ):

                importance = (
                    model.feature_importances_
                )

            elif hasattr(
                model,
                "coef_"
            ):

                coefficients = model.coef_

                if coefficients.ndim > 1:

                    importance = np.mean(
                        np.abs(
                            coefficients
                        ),
                        axis=0
                    )

                else:

                    importance = np.abs(
                        coefficients
                    )

            else:

                return pd.DataFrame(
                    columns=[
                        "feature",
                        "importance"
                    ]
                )

            result = pd.DataFrame({

                "feature":
                    feature_names,

                "importance":
                    importance

            })

            result[
                "importance_pct"
            ] = (

                result["importance"]
                /
                result["importance"].sum()
                * 100

            )

            result = (
                result
                .sort_values(
                    "importance",
                    ascending=False
                )
                .head(30)
                .reset_index(
                    drop=True
                )
            )

            result[
                "importance_pct"
            ] = result[
                "importance_pct"
            ].round(2)

            return result

        except Exception:

            return pd.DataFrame(
                columns=[
                    "feature",
                    "importance",
                    "importance_pct"
                ]
            )

    # =========================================================
    # SUMMARY
    # =========================================================

    @staticmethod
    def _summary(
        problem_type: str,
        target: str,
        best_model: str,
        successful: pd.DataFrame,
        feature_importance: pd.DataFrame
    ) -> dict[str, Any]:

        if problem_type == "regression":

            best_score = float(
                successful.iloc[0]["r2"]
            )

            score_name = "R²"

        else:

            best_score = float(
                successful.iloc[0]["f1"]
            )

            score_name = "F1"

        top_features = []

        if not feature_importance.empty:

            top_features = (
                feature_importance[
                    "feature"
                ]
                .head(5)
                .tolist()
            )

        return {

            "message":
                (
                    f"NEXUS trained and compared "
                    f"{len(successful)} predictive "
                    f"models for '{target}'."
                ),

            "problem_type":
                problem_type,

            "best_model":
                best_model,

            "best_score_name":
                score_name,

            "best_score":
                round(
                    best_score,
                    4
                ),

            "top_features":
                top_features
        }