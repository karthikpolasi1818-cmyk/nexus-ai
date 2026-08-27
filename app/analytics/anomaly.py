import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class AnomalyDetector:

    def detect(self, df, column):

        values = df[[column]].copy()

        values[column] = pd.to_numeric(
            values[column],
            errors="coerce"
        )

        values = values.dropna()

        if len(values) < 5:

            return values

        scaler = StandardScaler()

        X = scaler.fit_transform(
            values[[column]]
        )

        model = IsolationForest(
            contamination="auto",
            random_state=42
        )

        predictions = model.fit_predict(X)

        scores = model.decision_function(X)

        values["anomaly"] = (
            predictions == -1
        )

        values["anomaly_score"] = scores

        return values