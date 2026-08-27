from __future__ import annotations

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import (
    RandomForestRegressor,
    RandomForestClassifier,
    GradientBoostingRegressor,
    GradientBoostingClassifier,
)
from sklearn.linear_model import LinearRegression, LogisticRegression


class PredictionEngine:
    """
    NEXUS AI predictive analytics engine.

    Automatically:
    - detects regression/classification
    - prepares numerical/categorical features
    - handles missing values
    - encodes categorical data
    - trains multiple ML models
    - compares models
    - returns the best model
    """

    @staticmethod
    def detect_problem_type(
        df: pd.DataFrame,
        target: str
    ) -> str:

        if target not in df.columns:
            raise ValueError(
                f"Target column '{target}' does not exist."
            )

        series = df[target].dropna()

        if series.empty:
            raise ValueError(
                "Target column contains no usable values."
            )

        if (
            pd.api.types.is_object_dtype(series)
            or pd.api.types.is_bool_dtype(series)
            or pd.api.types.is_categorical_dtype(series)
        ):
            return "classification"

        unique_values = series.nunique()

        # Small number of unique numeric values
        # is usually classification.
        if unique_values <= 10:
            return "classification"

        return "regression"

    @staticmethod
    def prepare_data(
        df: pd.DataFrame,
        target: str
    ):

        working = df.copy()

        working = working.dropna(
            axis=0,
            how="all"
        )

        if target not in working.columns:
            raise ValueError(
                f"Target column '{target}' not found."
            )

        working = working.dropna(
            subset=[target]
        )

        X = working.drop(
            columns=[target]
        )

        y = working[target]

        # Remove columns with no information.
        constant_columns = [
            col
            for col in X.columns
            if X[col].nunique(dropna=False) <= 1
        ]

        if constant_columns:
            X = X.drop(
                columns=constant_columns
            )

        # Remove extremely high-cardinality text columns
        # such as IDs when appropriate.
        high_cardinality = []

        for column in X.select_dtypes(
            include=["object", "category"]
        ).columns:

            ratio = (
                X[column].nunique(dropna=True)
                / max(len(X), 1)
            )

            if ratio > 0.95:
                high_cardinality.append(column)

        if high_cardinality:
            X = X.drop(
                columns=high_cardinality
            )

        numeric_features = (
            X.select_dtypes(
                include=["number", "bool"]
            )
            .columns
            .tolist()
        )

        categorical_features = (
            X.select_dtypes(
                include=["object", "category"]
            )
            .columns
            .tolist()
        )

        numeric_pipeline = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(
                        strategy="median"
                    )
                )
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
                )
            ]
        )

        transformers = []

        if numeric_features:
            transformers.append(
                (
                    "numeric",
                    numeric_pipeline,
                    numeric_features
                )
            )

        if categorical_features:
            transformers.append(
                (
                    "categorical",
                    categorical_pipeline,
                    categorical_features
                )
            )

        if not transformers:
            raise ValueError(
                "No usable feature columns were detected."
            )

        preprocessor = ColumnTransformer(
            transformers=transformers,
            remainder="drop"
        )

        return (
            X,
            y,
            preprocessor,
            numeric_features,
            categorical_features
        )

    @staticmethod
    def _regression_models():

        return {
            "Linear Regression":
                LinearRegression(),

            "Random Forest":
                RandomForestRegressor(
                    n_estimators=250,
                    random_state=42,
                    n_jobs=-1
                ),

            "Gradient Boosting":
                GradientBoostingRegressor(
                    random_state=42
                )
        }

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
                    random_state=42
                )
        }

    @staticmethod
    def train(
        df: pd.DataFrame,
        target: str,
        test_size: float = 0.20,
        random_state: int = 42
    ) -> dict:

        if len(df) < 10:
            raise ValueError(
                "At least 10 rows are recommended for ML prediction."
            )

        (
            X,
            y,
            preprocessor,
            numeric_features,
            categorical_features
        ) = PredictionEngine.prepare_data(
            df,
            target
        )

        problem_type = (
            PredictionEngine
            .detect_problem_type(
                df,
                target
            )
        )

        if problem_type == "classification":

            if y.nunique() < 2:
                raise ValueError(
                    "Classification requires at least two target classes."
                )

            models = (
                PredictionEngine
                ._classification_models()
            )

            stratify = y if y.value_counts().min() >= 2 else None

        else:

            models = (
                PredictionEngine
                ._regression_models()
            )

            stratify = None

        X_train, X_test, y_train, y_test = (
            train_test_split(
                X,
                y,
                test_size=test_size,
                random_state=random_state,
                stratify=stratify
            )
        )

        results = []

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
                        )
                    ]
                )

                pipeline.fit(
                    X_train,
                    y_train
                )

                predictions = pipeline.predict(
                    X_test
                )

                if problem_type == "regression":

                    mae = mean_absolute_error(
                        y_test,
                        predictions
                    )

                    rmse = np.sqrt(
                        mean_squared_error(
                            y_test,
                            predictions
                        )
                    )

                    r2 = r2_score(
                        y_test,
                        predictions
                    )

                    results.append(
                        {
                            "model": model_name,
                            "MAE": round(
                                float(mae),
                                4
                            ),
                            "RMSE": round(
                                float(rmse),
                                4
                            ),
                            "R2": round(
                                float(r2),
                                4
                            ),
                            "score": round(
                                float(r2),
                                4
                            )
                        }
                    )

                else:

                    accuracy = (
                        np.mean(
                            predictions
                            == y_test
                        )
                    )

                    results.append(
                        {
                            "model": model_name,
                            "Accuracy": round(
                                float(accuracy),
                                4
                            ),
                            "score": round(
                                float(accuracy),
                                4
                            )
                        }
                    )

                trained_models[
                    model_name
                ] = pipeline

            except Exception as error:

                results.append(
                    {
                        "model": model_name,
                        "error": str(error),
                        "score": -np.inf
                    }
                )

        results_df = pd.DataFrame(
            results
        )

        valid_results = results_df[
            np.isfinite(
                results_df["score"]
            )
        ]

        if valid_results.empty:
            raise RuntimeError(
                "NEXUS could not successfully train any ML model."
            )

        best_model_name = (
            valid_results
            .sort_values(
                "score",
                ascending=False
            )
            .iloc[0]["model"]
        )

        best_model = trained_models[
            best_model_name
        ]

        return {

            "problem_type":
                problem_type,

            "target":
                target,

            "best_model":
                best_model_name,

            "best_pipeline":
                best_model,

            "comparison":
                results_df,

            "rows":
                len(df),

            "features":
                X.shape[1],

            "numeric_features":
                numeric_features,

            "categorical_features":
                categorical_features,

            "train_rows":
                len(X_train),

            "test_rows":
                len(X_test)
        }

    @staticmethod
    def predict(
        trained_result: dict,
        dataframe: pd.DataFrame
    ) -> pd.DataFrame:

        target = trained_result["target"]

        model = trained_result[
            "best_pipeline"
        ]

        X = dataframe.drop(
            columns=[target],
            errors="ignore"
        )

        predictions = model.predict(X)

        output = dataframe.copy()

        output[
            "NEXUS_PREDICTION"
        ] = predictions

        return output

    @staticmethod
    def feature_importance(
        trained_result: dict
    ) -> pd.DataFrame:

        pipeline = trained_result[
            "best_pipeline"
        ]

        model = pipeline.named_steps[
            "model"
        ]

        preprocessor = pipeline.named_steps[
            "preprocessor"
        ]

        try:

            feature_names = (
                preprocessor
                .get_feature_names_out()
            )

        except Exception:

            feature_names = [
                f"feature_{i}"
                for i in range(
                    len(
                        getattr(
                            model,
                            "feature_importances_",
                            []
                        )
                    )
                )
            ]

        if hasattr(
            model,
            "feature_importances_"
        ):

            importance = (
                model
                .feature_importances_
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

            return pd.DataFrame()

        result = pd.DataFrame(
            {
                "feature":
                    feature_names,

                "importance":
                    importance
            }
        )

        return (
            result
            .sort_values(
                "importance",
                ascending=False
            )
            .reset_index(
                drop=True
            )
        )

    @staticmethod
    def summary(
        trained_result: dict
    ) -> str:

        problem = trained_result[
            "problem_type"
        ]

        model = trained_result[
            "best_model"
        ]

        target = trained_result[
            "target"
        ]

        comparison = trained_result[
            "comparison"
        ]

        best_row = comparison[
            comparison["model"]
            == model
        ]

        if problem == "regression":

            score = float(
                best_row.iloc[0]["R2"]
            )

            return (
                f"NEXUS trained a regression model "
                f"to predict '{target}'. "
                f"The best model was {model} "
                f"with R² = {score:.3f}."
            )

        score = float(
            best_row.iloc[0]["Accuracy"]
        )

        return (
            f"NEXUS trained a classification model "
            f"to predict '{target}'. "
            f"The best model was {model} "
            f"with accuracy = {score:.1%}."
        )