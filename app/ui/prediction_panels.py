from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from app.analytics.prediction import PredictionEngine


class PredictionPanels:

    @staticmethod
    def predictive_intelligence(
        dataframe: pd.DataFrame | None
    ):

        st.subheader(
            "🔮 Predictive Intelligence"
        )

        if dataframe is None or dataframe.empty:

            st.info(
                "Upload a dataset to activate predictive intelligence."
            )

            return

        numeric = (
            dataframe
            .select_dtypes(
                include="number"
            )
            .columns
            .tolist()
        )

        categorical = (
            dataframe
            .select_dtypes(
                exclude="number"
            )
            .columns
            .tolist()
        )

        all_columns = (
            numeric +
            categorical
        )

        if not all_columns:

            st.warning(
                "No usable columns detected."
            )

            return

        target_candidates = []

        for column in all_columns:

            name = column.lower()

            if any(
                keyword in name
                for keyword in [
                    "sales",
                    "revenue",
                    "profit",
                    "price",
                    "demand",
                    "target",
                    "churn",
                    "class",
                    "score"
                ]
            ):

                target_candidates.append(
                    column
                )

        default_target = (
            target_candidates[0]
            if target_candidates
            else all_columns[-1]
        )

        target = st.selectbox(
            "🎯 Prediction Target",
            all_columns,
            index=all_columns.index(
                default_target
            ),
            key="prediction_target"
        )

        st.caption(
            "NEXUS will automatically determine whether "
            "this is a regression or classification problem."
        )

        if st.button(
            "🚀 Train NEXUS Prediction Models",
            type="primary",
            key="train_prediction_models"
        ):

            with st.spinner(
                "🧠 Training and comparing ML models..."
            ):

                try:

                    result = (
                        PredictionEngine
                        .train(
                            dataframe,
                            target
                        )
                    )

                    st.session_state[
                        "nexus_prediction_result"
                    ] = result

                    st.success(
                        "Prediction models trained successfully."
                    )

                except Exception as error:

                    st.error(
                        f"Prediction failed: {error}"
                    )

        result = st.session_state.get(
            "nexus_prediction_result"
        )

        if not result:

            return

        if result["target"] != target:

            return

        st.divider()

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Problem Type",
            result["problem_type"].title()
        )

        c2.metric(
            "Best Model",
            result["best_model"]
        )

        c3.metric(
            "Training Rows",
            f"{result['train_rows']:,}"
        )

        c4.metric(
            "Test Rows",
            f"{result['test_rows']:,}"
        )

        st.markdown(
            "### 🏆 Model Competition"
        )

        comparison = result[
            "comparison"
        ].copy()

        display_columns = [
            column
            for column in comparison.columns
            if column != "score"
        ]

        st.dataframe(
            comparison[
                display_columns
            ],
            width="stretch",
            hide_index=True
        )

        st.markdown(
            "### 🧬 Feature Importance"
        )

        importance = (
            PredictionEngine
            .feature_importance(
                result
            )
        )

        if not importance.empty:

            top_features = (
                importance
                .head(15)
            )

            figure = px.bar(
                top_features,
                x="importance",
                y="feature",
                orientation="h",
                title="Top Predictive Features"
            )

            figure.update_layout(
                yaxis={
                    "categoryorder":
                    "total ascending"
                }
            )

            st.plotly_chart(
                figure,
                width="stretch"
            )

            st.dataframe(
                importance,
                width="stretch",
                hide_index=True
            )

        st.markdown(
            "### 🧠 NEXUS Model Explanation"
        )

        st.info(
            PredictionEngine.summary(
                result
            )
        )

        st.markdown(
            "### 🔮 Generate Predictions"
        )

        if st.button(
            "Generate Predictions",
            key="generate_nexus_predictions"
        ):

            try:

                prediction_data = (
                    PredictionEngine
                    .predict(
                        result,
                        dataframe
                    )
                )

                st.dataframe(
                    prediction_data,
                    width="stretch",
                    hide_index=True
                )

                csv = (
                    prediction_data
                    .to_csv(
                        index=False
                    )
                    .encode("utf-8")
                )

                st.download_button(
                    "⬇️ Download Predictions CSV",
                    data=csv,
                    file_name="nexus_predictions.csv",
                    mime="text/csv",
                    key="download_predictions"
                )

            except Exception as error:

                st.error(
                    f"Prediction generation failed: {error}"
                )