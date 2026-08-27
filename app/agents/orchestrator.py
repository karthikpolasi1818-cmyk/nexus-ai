from app.analytics.profiling import DataProfiler
from app.analytics.cleaning import DataCleaner
from app.analytics.kpi import KPIEngine
from app.agents.insight_agent import InsightAgent


class AutonomousOrchestrator:

    def __init__(self):

        self.profiler = DataProfiler()
        self.cleaner = DataCleaner()
        self.kpi_engine = KPIEngine()
        self.insight_agent = InsightAgent()

    def execute(self, df):

        # Agent 1
        profile = (
            self.profiler
            .profile(df)
        )

        # Agent 2
        quality = (
            self.cleaner
            .analyze(df)
        )

        # Agent 3
        cleaned_df = (
            self.cleaner
            .clean(df)
        )

        # Agent 4
        kpis = (
            self.kpi_engine
            .calculate(cleaned_df)
        )

        # Agent 5
        insights = (
            self.insight_agent
            .generate(
                cleaned_df,
                profile,
                kpis
            )
        )

        return {
            "profile": profile,
            "quality": quality,
            "cleaned_data": cleaned_df,
            "kpis": kpis,
            "insights": insights
        }