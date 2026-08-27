class KPIEngine:

    def calculate(self, df):

        numeric = df.select_dtypes(
            include="number"
        )

        kpis = {}

        for column in numeric.columns:

            kpis[column] = {
                "total": float(
                    numeric[column].sum()
                ),
                "average": float(
                    numeric[column].mean()
                ),
                "median": float(
                    numeric[column].median()
                ),
                "minimum": float(
                    numeric[column].min()
                ),
                "maximum": float(
                    numeric[column].max()
                )
            }

        columns = {
            column.lower(): column
            for column in df.columns
        }

        revenue = None
        profit = None

        for name, column in columns.items():

            if any(
                word in name
                for word in [
                    "sales",
                    "revenue",
                    "amount"
                ]
            ):

                revenue = column
                break

        for name, column in columns.items():

            if "profit" in name:

                profit = column
                break

        if revenue:

            kpis["TOTAL_REVENUE"] = float(
                df[revenue].sum()
            )

        if profit:

            kpis["TOTAL_PROFIT"] = float(
                df[profit].sum()
            )

        if revenue and profit:

            revenue_value = df[revenue].sum()
            profit_value = df[profit].sum()

            if revenue_value != 0:

                kpis["PROFIT_MARGIN"] = float(
                    profit_value /
                    revenue_value *
                    100
                )

        return kpis