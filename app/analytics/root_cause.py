from __future__ import annotations

import pandas as pd


def root_cause_analysis(
    df: pd.DataFrame,
    target: str,
    dimensions: list[str] | None = None,
    top_n: int = 10
) -> dict:

    if target not in df.columns:

        raise ValueError(
            f"Target '{target}' not found."
        )

    dimensions = dimensions or [

        column

        for column
        in df.select_dtypes(
            exclude="number"
        ).columns

        if column != target
    ]

    y = pd.to_numeric(
        df[target],
        errors="coerce"
    )

    work = df.copy()

    work["_target"] = y

    work = work.dropna(
        subset=[
            "_target"
        ]
    )

    overall_mean = float(
        work["_target"].mean()
    )

    total = float(
        work["_target"].sum()
    )

    drivers = []

    for dimension in dimensions:

        if dimension not in work.columns:
            continue

        grouped = (

            work

            .groupby(
                dimension,
                dropna=False
            )["_target"]

            .agg([
                "sum",
                "mean",
                "count"
            ])

            .reset_index()
        )

        grouped[
            "share_of_total"
        ] = (

            grouped["sum"]
            / total

            if total != 0

            else 0
        )

        grouped[
            "vs_overall_pct"
        ] = (

            (
                grouped["mean"]
                - overall_mean
            )

            /

            (
                abs(
                    overall_mean
                )
                + 1e-9
            )

            * 100
        )

        grouped[
            "dimension"
        ] = dimension

        grouped[
            "segment"
        ] = grouped[
            dimension
        ].astype(str)

        drivers.append(

            grouped[
                [
                    "dimension",
                    "segment",
                    "sum",
                    "mean",
                    "count",
                    "share_of_total",
                    "vs_overall_pct"
                ]
            ]
        )

    if not drivers:

        return {

            "overall_mean":
                overall_mean,

            "drivers":
                pd.DataFrame()
        }

    result = pd.concat(
        drivers,
        ignore_index=True
    )

    result[
        "impact_score"
    ] = (

        result[
            "share_of_total"
        ].abs()

        *

        result[
            "vs_overall_pct"
        ].abs()
    )

    result = (

        result

        .sort_values(
            "impact_score",
            ascending=False
        )

        .head(top_n)

        .reset_index(
            drop=True
        )
    )

    return {

        "overall_mean":
            overall_mean,

        "total":
            total,

        "drivers":
            result,

        "interpretation":
            (
                "These are statistical business drivers/segments. "
                "They should not be treated as proof of causality."
            )
    }