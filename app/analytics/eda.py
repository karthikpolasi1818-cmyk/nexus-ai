class EDAEngine:

    def group_analysis(
        self,
        df,
        dimension,
        metric
    ):

        result = (
            df.groupby(dimension)[metric]
            .agg([
                "sum",
                "mean",
                "count"
            ])
            .reset_index()
            .sort_values(
                "sum",
                ascending=False
            )
        )

        return result

    def top_entities(
        self,
        df,
        dimension,
        metric,
        n=10
    ):

        result = self.group_analysis(
            df,
            dimension,
            metric
        )

        return result.head(n)