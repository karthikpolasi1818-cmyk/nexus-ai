class CorrelationEngine:

    def calculate(self, df):

        numeric = df.select_dtypes(
            include="number"
        )

        if numeric.shape[1] < 2:

            return None

        return numeric.corr()