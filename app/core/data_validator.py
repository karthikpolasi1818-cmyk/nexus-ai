from __future__ import annotations

from typing import Any

import pandas as pd

from app.core.exceptions import (
    NexusDataError,
    NexusDataValidationError,
)


# ============================================================
# NEXUS DATA VALIDATOR
# ============================================================


class DataValidator:
    """
    Central validation layer for NEXUS AI datasets.

    Responsibilities:
        - Validate DataFrame input
        - Detect empty datasets
        - Detect missing column names
        - Detect duplicate column names
        - Validate target columns
        - Validate numeric targets
        - Produce structured validation results
    """

    # ========================================================
    # BASIC VALIDATION
    # ========================================================

    @staticmethod
    def validate_dataframe(
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:
        """
        Validate a DataFrame before analysis.

        Returns:
            Structured validation result.

        Raises:
            NexusDataValidationError:
                When the DataFrame is invalid.
        """

        if not isinstance(
            dataframe,
            pd.DataFrame,
        ):

            raise NexusDataValidationError(
                "Input must be a pandas DataFrame.",
                details={
                    "received_type": type(
                        dataframe
                    ).__name__,
                },
            )

        if dataframe.empty:

            raise NexusDataValidationError(
                "Dataset is empty.",
                details={
                    "rows": 0,
                    "columns": len(
                        dataframe.columns
                    ),
                },
            )

        if len(dataframe.columns) == 0:

            raise NexusDataValidationError(
                "Dataset contains no columns.",
                details={
                    "rows": len(dataframe),
                    "columns": 0,
                },
            )

        # ----------------------------------------------------
        # Column-name validation
        # ----------------------------------------------------

        invalid_columns = [
            column
            for column in dataframe.columns
            if column is None
            or not str(column).strip()
        ]

        if invalid_columns:

            raise NexusDataValidationError(
                "Dataset contains empty column names.",
                details={
                    "invalid_columns": [
                        str(column)
                        for column in invalid_columns
                    ],
                },
            )

        # ----------------------------------------------------
        # Duplicate columns
        # ----------------------------------------------------

        duplicate_columns = (
            dataframe.columns[
                dataframe.columns.duplicated()
            ]
            .astype(str)
            .tolist()
        )

        if duplicate_columns:

            raise NexusDataValidationError(
                "Dataset contains duplicate column names.",
                details={
                    "duplicate_columns": (
                        duplicate_columns
                    ),
                },
            )

        # ----------------------------------------------------
        # Missing values
        # ----------------------------------------------------

        missing_by_column = {
            str(column): int(
                dataframe[column]
                .isna()
                .sum()
            )
            for column in dataframe.columns
            if dataframe[column]
            .isna()
            .any()
        }

        total_missing = sum(
            missing_by_column.values()
        )

        # ----------------------------------------------------
        # Numeric / categorical information
        # ----------------------------------------------------

        numeric_columns = [
            str(column)
            for column in dataframe.select_dtypes(
                include="number"
            ).columns
        ]

        categorical_columns = [
            str(column)
            for column in dataframe.select_dtypes(
                include=[
                    "object",
                    "category",
                    "string",
                ]
            ).columns
        ]

        datetime_columns = [
            str(column)
            for column in dataframe.select_dtypes(
                include=[
                    "datetime",
                    "datetimetz",
                ]
            ).columns
        ]

        return {
            "valid": True,
            "status": (
                "warning"
                if total_missing > 0
                else "healthy"
            ),
            "rows": int(
                len(dataframe)
            ),
            "columns": int(
                len(dataframe.columns)
            ),
            "numeric_columns": numeric_columns,
            "categorical_columns": (
                categorical_columns
            ),
            "datetime_columns": (
                datetime_columns
            ),
            "missing_values": {
                "total": int(
                    total_missing
                ),
                "by_column": (
                    missing_by_column
                ),
            },
        }

    # ========================================================
    # TARGET VALIDATION
    # ========================================================

    @staticmethod
    def validate_target(
        dataframe: pd.DataFrame,
        target: str,
        *,
        require_numeric: bool = False,
    ) -> dict[str, Any]:
        """
        Validate an analysis target column.
        """

        DataValidator.validate_dataframe(
            dataframe
        )

        if target is None:

            raise NexusDataValidationError(
                "Target column was not provided."
            )

        target = str(
            target
        ).strip()

        if not target:

            raise NexusDataValidationError(
                "Target column cannot be empty."
            )

        if target not in dataframe.columns:

            raise NexusDataValidationError(
                f"Target column '{target}' "
                "does not exist in the dataset.",
                details={
                    "target": target,
                    "available_columns": [
                        str(column)
                        for column in dataframe.columns
                    ],
                },
            )

        series = dataframe[target]

        if series.dropna().empty:

            raise NexusDataValidationError(
                f"Target column '{target}' "
                "contains no usable values.",
                details={
                    "target": target,
                    "missing_values": int(
                        series.isna().sum()
                    ),
                },
            )

        if require_numeric and not pd.api.types.is_numeric_dtype(
            series
        ):

            raise NexusDataValidationError(
                f"Target column '{target}' "
                "must be numeric.",
                details={
                    "target": target,
                    "dtype": str(
                        series.dtype
                    ),
                },
            )

        return {
            "valid": True,
            "target": target,
            "dtype": str(
                series.dtype
            ),
            "rows": int(
                len(series)
            ),
            "missing_values": int(
                series.isna().sum()
            ),
            "unique_values": int(
                series.nunique(
                    dropna=True
                )
            ),
            "numeric": bool(
                pd.api.types.is_numeric_dtype(
                    series
                )
            ),
        }

    # ========================================================
    # ANALYSIS VALIDATION
    # ========================================================

    @staticmethod
    def validate_for_analysis(
        dataframe: pd.DataFrame,
        target: str | None = None,
    ) -> dict[str, Any]:
        """
        Perform complete pre-analysis validation.
        """

        dataframe_result = (
            DataValidator.validate_dataframe(
                dataframe
            )
        )

        target_result = None

        if target is not None:

            target_result = (
                DataValidator.validate_target(
                    dataframe,
                    target,
                )
            )

        return {
            "valid": True,
            "status": dataframe_result[
                "status"
            ],
            "dataframe": dataframe_result,
            "target": target_result,
        }

    # ========================================================
    # SAFE VALIDATION
    # ========================================================

    @staticmethod
    def safe_validate(
        dataframe: pd.DataFrame,
        target: str | None = None,
    ) -> dict[str, Any]:
        """
        Validation wrapper that never raises.

        Useful for UI/API layers.
        """

        try:

            return DataValidator.validate_for_analysis(
                dataframe,
                target,
            )

        except NexusDataError as error:

            return error.to_dict()

        except Exception as error:

            return {
                "valid": False,
                "error": (
                    "VALIDATION_INTERNAL_ERROR"
                ),
                "message": str(error),
            }


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================


def validate_dataframe(
    dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """Convenience wrapper."""

    return DataValidator.validate_dataframe(
        dataframe
    )


def validate_target(
    dataframe: pd.DataFrame,
    target: str,
    *,
    require_numeric: bool = False,
) -> dict[str, Any]:
    """Convenience wrapper."""

    return DataValidator.validate_target(
        dataframe,
        target,
        require_numeric=require_numeric,
    )


def validate_for_analysis(
    dataframe: pd.DataFrame,
    target: str | None = None,
) -> dict[str, Any]:
    """Convenience wrapper."""

    return DataValidator.validate_for_analysis(
        dataframe,
        target,
    )


__all__ = [
    "DataValidator",
    "validate_dataframe",
    "validate_target",
    "validate_for_analysis",
]