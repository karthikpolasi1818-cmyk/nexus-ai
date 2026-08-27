import pandas as pd


class DataProfiler:

    def profile(self, df):

        column_information = []

        for column in df.columns:

            series = df[column]

            if pd.api.types.is_numeric_dtype(series):
                semantic_type = "numeric"

            elif pd.api.types.is_datetime64_any_dtype(series):
                semantic_type = "datetime"

            else:
                semantic_type = "categorical"

            column_information.append({
                "column": column,
                "dtype": str(series.dtype),
                "semantic_type": semantic_type,
                "unique_values": int(
                    series.nunique(dropna=True)
                ),
                "missing": int(
                    series.isna().sum()
                ),
                "missing_percentage": round(
                    series.isna().mean() * 100,
                    2
                )
            })

        return {
            "rows": len(df),
            "columns": len(df.columns),
            "missing_values": int(
                df.isna().sum().sum()
            ),
            "duplicate_rows": int(
                df.duplicated().sum()
            ),
            "columns_info": column_information
        }