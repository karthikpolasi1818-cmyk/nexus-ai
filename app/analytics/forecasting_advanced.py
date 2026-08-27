from __future__ import annotations

import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error
)


def forecast_with_backtesting(
    df: pd.DataFrame,
    date_column: str,
    target_column: str,
    periods: int = 14,
    lags: int = 7
) -> dict:

    work = df[
        [
            date_column,
            target_column
        ]
    ].copy()

    work[date_column] = pd.to_datetime(
        work[date_column],
        errors="coerce"
    )

    work[target_column] = pd.to_numeric(
        work[target_column],
        errors="coerce"
    )

    work = (
        work
        .dropna()
        .groupby(
            date_column,
            as_index=False
        )[target_column]
        .sum()
        .sort_values(
            date_column
        )
    )

    if len(work) < max(
        30,
        lags + 10
    ):

        return {

            "forecast":
                pd.DataFrame(),

            "metrics": {},

            "message":
                "Need more historical observations for ML forecasting."
        }

    y = work[
        target_column
    ].astype(float).reset_index(
        drop=True
    )

    features = []

    targets = []

    for i in range(
        lags,
        len(y)
    ):

        row = {

            f"lag_{j}":
                float(
                    y.iloc[i - j]
                )

            for j
            in range(
                1,
                lags + 1
            )
        }

        row[
            "rolling_mean_7"
        ] = float(
            y.iloc[
                max(0, i - 7):i
            ].mean()
        )

        row[
            "rolling_std_7"
        ] = float(
            y.iloc[
                max(0, i - 7):i
            ].std(
                ddof=0
            )
        )

        features.append(
            row
        )

        targets.append(
            float(
                y.iloc[i]
            )
        )

    X = pd.DataFrame(
        features
    ).fillna(0)

    yy = np.array(
        targets
    )

    split = max(
        int(
            len(X) * 0.80
        ),
        len(X) - 14
    )

    split = min(
        max(
            split,
            10
        ),
        len(X) - 1
    )

    X_train = X.iloc[
        :split
    ]

    X_test = X.iloc[
        split:
    ]

    y_train = yy[
        :split
    ]

    y_test = yy[
        split:
    ]

    model = RandomForestRegressor(

        n_estimators=300,

        random_state=42,

        n_jobs=-1,

        min_samples_leaf=2
    )

    model.fit(
        X_train,
        y_train
    )

    predictions = model.predict(
        X_test
    )

    mae = float(
        mean_absolute_error(
            y_test,
            predictions
        )
    )

    rmse = float(
        np.sqrt(
            mean_squared_error(
                y_test,
                predictions
            )
        )
    )

    # ==========================================================
    # FUTURE FORECAST
    # ==========================================================

    history = list(
        y.astype(float)
    )

    future_values = []

    for _ in range(
        periods
    ):

        values = history[
            -lags:
        ]

        row = {

            f"lag_{j}":
                float(
                    values[-j]
                )

            for j
            in range(
                1,
                lags + 1
            )
        }

        row[
            "rolling_mean_7"
        ] = float(
            np.mean(
                history[-7:]
            )
        )

        row[
            "rolling_std_7"
        ] = float(
            np.std(
                history[-7:]
            )
        )

        next_value = float(
            model.predict(
                pd.DataFrame(
                    [row]
                ).fillna(0)
            )[0]
        )

        next_value = max(
            0.0,
            next_value
        )

        future_values.append(
            next_value
        )

        history.append(
            next_value
        )

    last_date = work[
        date_column
    ].max()

    dates = pd.date_range(

        last_date
        + pd.Timedelta(
            days=1
        ),

        periods=periods,

        freq="D"
    )

    forecast = pd.DataFrame({

        "date": dates,

        "forecast":
            future_values
    })

    return {

        "forecast":
            forecast,

        "metrics": {

            "MAE":
                round(
                    mae,
                    4
                ),

            "RMSE":
                round(
                    rmse,
                    4
                ),

            "test_points":
                len(y_test)
        },

        "message":
            "Forecast generated with chronological backtesting."
    }