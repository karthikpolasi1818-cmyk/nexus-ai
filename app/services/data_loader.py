from pathlib import Path
import pandas as pd


class DataLoader:

    SUPPORTED_FORMATS = [
        ".csv",
        ".xlsx",
        ".xls",
        ".json",
        ".parquet"
    ]

    @staticmethod
    def load(file):

        filename = file.name.lower()
        extension = Path(filename).suffix

        if extension == ".csv":
            return pd.read_csv(file)

        if extension in [".xlsx", ".xls"]:
            return pd.read_excel(file)

        if extension == ".json":
            return pd.read_json(file)

        if extension == ".parquet":
            return pd.read_parquet(file)

        raise ValueError(
            f"Unsupported file format: {extension}"
        )

    @staticmethod
    def validate(df):

        if df is None:
            raise ValueError("Dataset is empty.")

        if df.empty:
            raise ValueError(
                "Dataset contains no rows."
            )

        if len(df.columns) == 0:
            raise ValueError(
                "Dataset contains no columns."
            )

        return True