class InsightAgent:

    def generate(
        self,
        df,
        profile,
        kpis,
        anomaly_results=None
    ):

        insights = []

        insights.append(
            f"The dataset contains "
            f"{profile['rows']:,} records "
            f"across "
            f"{profile['columns']} columns."
        )

        missing = profile[
            "missing_values"
        ]

        if missing == 0:

            insights.append(
                "No missing values were detected."
            )

        else:

            insights.append(
                f"{missing:,} missing values "
                "were detected."
            )

        duplicates = profile[
            "duplicate_rows"
        ]

        if duplicates > 0:

            insights.append(
                f"{duplicates:,} duplicate "
                "records were detected."
            )

        if "TOTAL_REVENUE" in kpis:

            insights.append(
                f"Total detected revenue is "
                f"{kpis['TOTAL_REVENUE']:,.2f}."
            )

        if "TOTAL_PROFIT" in kpis:

            insights.append(
                f"Total detected profit is "
                f"{kpis['TOTAL_PROFIT']:,.2f}."
            )

        if "PROFIT_MARGIN" in kpis:

            insights.append(
                f"Detected profit margin is "
                f"{kpis['PROFIT_MARGIN']:.2f}%."
            )

        return insights