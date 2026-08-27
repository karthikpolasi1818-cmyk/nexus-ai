import pandas as pd
import numpy as np


class DataCleaner:

    def analyze(self, df):

        issues = []

        duplicate_count = int(
            df.duplicated().sum()
        )

        if duplicate_count > 0:

            issues.append({
                "issue": "Duplicate Rows",
                "count": duplicate_count,
                "severity": "Medium",
                "recommendation":
                    "Remove duplicate records."
            })

        for column in df.columns:

            missing = int(
                df[column].isna().sum()
            )

            if missing > 0:

                percentage = (
                    missing / len(df) * 100
                )

                if percentage >= 30:
                    severity = "Critical"

                elif percentage >= 10:
                    severity = "High"

                elif percentage >= 5:
                    severity = "Medium"

                else:
                    severity = "Low"

                issues.append({
                    "column": column,
                    "issue": "Missing Values",
                    "count": missing,
                    "percentage": round(
                        percentage,
                        2
                    ),
                    "severity": severity,
                    "recommendation":
                        "Apply appropriate imputation."
                })

        return issues

    def clean(self, df):

        result = df.copy()

        # Clean column names
        result.columns = [
            str(column).strip()
            for column in result.columns
        ]

        # Remove duplicates
        result = result.drop_duplicates()

        # Detect date columns
        for column in result.columns:

            column_name = column.lower()

            if (
                "date" in column_name
                or "time" in column_name
            ):

                converted = pd.to_datetime(
                    result[column],
                    errors="coerce"
                )

                if converted.notna().mean() >= 0.7:
                    result[column] = converted

        # Numeric missing values
        numerical_columns = result.select_dtypes(
            include=np.number
        ).columns

        for column in numerical_columns:

            if result[column].isna().any():

                median = result[column].median()

                result[column] = (
                    result[column]
                    .fillna(median)
                )

        # Categorical missing values
        categorical_columns = result.select_dtypes(
            exclude=np.number
        ).columns

        for column in categorical_columns:

            if result[column].isna().any():

                mode = result[column].mode()

                if not mode.empty:

                    result[column] = (
                        result[column]
                        .fillna(mode.iloc[0])
                    )

                else:

                    result[column] = (
                        result[column]
                        .fillna("Unknown")
                    )

        return result