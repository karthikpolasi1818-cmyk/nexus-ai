from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import numpy as np
import pandas as pd


# ============================================================
# SCENARIO
# ============================================================

@dataclass
class Scenario:

    name: str

    price_change_pct: float = 0.0
    demand_change_pct: float = 0.0
    marketing_change_pct: float = 0.0
    variable_cost_change_pct: float = 0.0
    fixed_cost_change_pct: float = 0.0

    def to_dict(self) -> dict[str, Any]:

        return asdict(self)


# ============================================================
# DECISION INTELLIGENCE
# ============================================================

class DecisionIntelligence:
    """
    NEXUS AI Decision Intelligence Engine.

    Provides:

    - Business metric discovery
    - Scenario simulation
    - What-if analysis
    - Risk scoring
    - Confidence scoring
    - Scenario ranking
    - Sensitivity analysis
    - Break-even analysis
    - Executive recommendations
    """

    VERSION = "4.0.0"

    # ========================================================
    # SAFE HELPERS
    # ========================================================

    @staticmethod
    def _safe_float(
        value: Any,
        default: float = 0.0,
    ) -> float:

        try:

            value = float(value)

            if np.isfinite(value):

                return value

        except (
            TypeError,
            ValueError,
        ):

            pass

        return default

    @staticmethod
    def _find_column(
        df: pd.DataFrame,
        candidates: list[str],
    ) -> str | None:

        lookup = {
            str(column).strip().lower(): column
            for column in df.columns
        }

        for candidate in candidates:

            if candidate.lower() in lookup:

                return lookup[
                    candidate.lower()
                ]

        # Partial matching

        for column in df.columns:

            column_name = (
                str(column)
                .strip()
                .lower()
            )

            for candidate in candidates:

                if candidate.lower() in column_name:

                    return column

        return None

    # ========================================================
    # BUSINESS METRIC DISCOVERY
    # ========================================================

    @classmethod
    def discover_business_metrics(
        cls,
        df: pd.DataFrame,
    ) -> dict[str, Any]:

        numeric = (
            df
            .select_dtypes(
                include="number"
            )
            .columns
            .tolist()
        )

        revenue_column = cls._find_column(
            df,
            [
                "sales",
                "revenue",
                "total_sales",
                "amount",
                "turnover",
            ],
        )

        profit_column = cls._find_column(
            df,
            [
                "profit",
                "net_profit",
                "gross_profit",
                "operating_profit",
            ],
        )

        quantity_column = cls._find_column(
            df,
            [
                "quantity",
                "qty",
                "units",
                "volume",
            ],
        )

        metrics: dict[str, Any] = {

            "revenue_column":
                revenue_column,

            "profit_column":
                profit_column,

            "quantity_column":
                quantity_column,

            "numeric_columns":
                numeric,

            "TOTAL_REVENUE":
                0.0,

            "TOTAL_PROFIT":
                0.0,

            "PROFIT_MARGIN":
                0.0,

            "TOTAL_QUANTITY":
                0.0,

            "AVERAGE_REVENUE":
                0.0,

            "AVERAGE_PROFIT":
                0.0,
        }

        if revenue_column:

            revenue_series = pd.to_numeric(
                df[revenue_column],
                errors="coerce",
            ).fillna(0)

            revenue = float(
                revenue_series.sum()
            )

            metrics[
                "TOTAL_REVENUE"
            ] = round(
                revenue,
                2,
            )

            metrics[
                "AVERAGE_REVENUE"
            ] = round(
                float(
                    revenue_series.mean()
                ),
                2,
            )

        if profit_column:

            profit_series = pd.to_numeric(
                df[profit_column],
                errors="coerce",
            ).fillna(0)

            profit = float(
                profit_series.sum()
            )

            metrics[
                "TOTAL_PROFIT"
            ] = round(
                profit,
                2,
            )

            metrics[
                "AVERAGE_PROFIT"
            ] = round(
                float(
                    profit_series.mean()
                ),
                2,
            )

        if quantity_column:

            quantity_series = pd.to_numeric(
                df[quantity_column],
                errors="coerce",
            ).fillna(0)

            metrics[
                "TOTAL_QUANTITY"
            ] = round(
                float(
                    quantity_series.sum()
                ),
                2,
            )

        revenue = metrics[
            "TOTAL_REVENUE"
        ]

        profit = metrics[
            "TOTAL_PROFIT"
        ]

        if abs(revenue) > 1e-12:

            metrics[
                "PROFIT_MARGIN"
            ] = round(
                profit
                / revenue
                * 100,
                2,
            )

        return metrics

    # ========================================================
    # SIMULATION
    # ========================================================

    @classmethod
    def simulate(
        cls,
        revenue: float,
        profit: float,
        scenario: Scenario,
        demand_elasticity: float = -0.30,
        marketing_roi: float = 0.25,
    ) -> dict[str, Any]:

        revenue = max(
            cls._safe_float(revenue),
            0,
        )

        profit = cls._safe_float(
            profit
        )

        # ----------------------------------------------------
        # PRICE
        # ----------------------------------------------------

        price_factor = (
            1
            + scenario.price_change_pct
            / 100
        )

        # ----------------------------------------------------
        # DEMAND
        # ----------------------------------------------------

        demand_factor = (

            1

            + scenario.demand_change_pct
            / 100

            + demand_elasticity
            *
            scenario.price_change_pct
            / 100
        )

        demand_factor = max(
            demand_factor,
            0,
        )

        # ----------------------------------------------------
        # MARKETING
        # ----------------------------------------------------

        marketing_factor = (

            1

            + (
                scenario.marketing_change_pct
                / 100
            )
            * marketing_roi
        )

        marketing_factor = max(
            marketing_factor,
            0,
        )

        # ----------------------------------------------------
        # REVENUE
        # ----------------------------------------------------

        new_revenue = (

            revenue

            * price_factor

            * demand_factor

            * marketing_factor
        )

        # ----------------------------------------------------
        # BASE COST STRUCTURE
        # ----------------------------------------------------

        margin = (

            profit / revenue

            if revenue
            else 0
        )

        variable_cost = (

            revenue
            * (1 - margin)
        )

        fixed_cost = max(
            revenue
            - variable_cost
            - profit,
            0,
        )

        # ----------------------------------------------------
        # COST CHANGES
        # ----------------------------------------------------

        new_variable_cost = (

            variable_cost

            * (

                1

                + scenario.variable_cost_change_pct
                / 100
            )
        )

        new_fixed_cost = (

            fixed_cost

            * (

                1

                + scenario.fixed_cost_change_pct
                / 100
            )
        )

        # ----------------------------------------------------
        # SCALE VARIABLE COST
        # ----------------------------------------------------

        revenue_ratio = (

            new_revenue / revenue

            if revenue
            else 1
        )

        scaled_variable_cost = (

            new_variable_cost
            * revenue_ratio
        )

        # ----------------------------------------------------
        # PROFIT
        # ----------------------------------------------------

        new_profit = (

            new_revenue

            - scaled_variable_cost

            - new_fixed_cost
        )

        # ----------------------------------------------------
        # MARGIN
        # ----------------------------------------------------

        new_margin = (

            new_profit
            / new_revenue
            * 100

            if new_revenue
            else 0
        )

        base_margin_pct = (

            margin * 100
        )

        revenue_change = (

            (
                new_revenue
                / revenue
                - 1
            )
            * 100

            if revenue
            else 0
        )

        profit_change = (

            (
                new_profit
                / profit
                - 1
            )
            * 100

            if abs(profit) > 1e-12

            else 0
        )

        margin_change = (

            new_margin
            - base_margin_pct
        )

        # ----------------------------------------------------
        # RISK
        # ----------------------------------------------------

        risk = cls._risk_score(
            revenue_change,
            profit_change,
            margin_change,
            scenario,
        )

        # ----------------------------------------------------
        # CONFIDENCE
        # ----------------------------------------------------

        confidence = cls._confidence_score(
            scenario,
            demand_elasticity,
            marketing_roi,
        )

        # ----------------------------------------------------
        # DECISION SCORE
        # ----------------------------------------------------

        decision_score = (

            profit_change * 0.55

            + revenue_change * 0.25

            + margin_change * 0.20

            - risk * 0.15
        )

        if decision_score >= 15:

            decision = (
                "STRONGLY RECOMMENDED"
            )

        elif decision_score >= 5:

            decision = (
                "RECOMMENDED"
            )

        elif decision_score >= 0:

            decision = (
                "NEUTRAL"
            )

        elif decision_score >= -10:

            decision = (
                "CAUTION"
            )

        else:

            decision = (
                "NOT RECOMMENDED"
            )

        return {

            **scenario.to_dict(),

            "revenue":
                round(
                    new_revenue,
                    2,
                ),

            "profit":
                round(
                    new_profit,
                    2,
                ),

            "margin_pct":
                round(
                    new_margin,
                    2,
                ),

            "revenue_change_pct":
                round(
                    revenue_change,
                    2,
                ),

            "profit_change_pct":
                round(
                    profit_change,
                    2,
                ),

            "margin_change_pct":
                round(
                    margin_change,
                    2,
                ),

            "risk_score":
                round(
                    risk,
                    2,
                ),

            "confidence_score":
                round(
                    confidence,
                    2,
                ),

            "decision_score":
                round(
                    decision_score,
                    2,
                ),

            "decision":
                decision,
        }

    # ========================================================
    # RISK
    # ========================================================

    @staticmethod
    def _risk_score(
        revenue_change: float,
        profit_change: float,
        margin_change: float,
        scenario: Scenario,
    ) -> float:

        risk = 0.0

        if profit_change < 0:

            risk += min(
                abs(profit_change)
                * 0.5,
                40,
            )

        if revenue_change < 0:

            risk += min(
                abs(revenue_change)
                * 0.2,
                20,
            )

        if margin_change < -5:

            risk += min(
                abs(margin_change),
                20,
            )

        changes = [

            abs(
                scenario.price_change_pct
            ),

            abs(
                scenario.demand_change_pct
            ),

            abs(
                scenario.marketing_change_pct
            ),

            abs(
                scenario.variable_cost_change_pct
            ),

            abs(
                scenario.fixed_cost_change_pct
            ),
        ]

        if max(changes) > 30:

            risk += 10

        if max(changes) > 50:

            risk += 15

        return min(
            max(
                risk,
                0,
            ),
            100,
        )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    @staticmethod
    def _confidence_score(
        scenario: Scenario,
        demand_elasticity: float,
        marketing_roi: float,
    ) -> float:

        confidence = 100.0

        assumption_size = np.mean([

            abs(
                scenario.price_change_pct
            ),

            abs(
                scenario.demand_change_pct
            ),

            abs(
                scenario.marketing_change_pct
            ),

            abs(
                scenario.variable_cost_change_pct
            ),

            abs(
                scenario.fixed_cost_change_pct
            ),
        ])

        confidence -= min(
            assumption_size * 0.5,
            35,
        )

        if abs(
            demand_elasticity
        ) > 1:

            confidence -= 10

        if abs(
            marketing_roi
        ) > 1:

            confidence -= 10

        return max(
            min(
                confidence,
                100,
            ),
            0,
        )

    # ========================================================
    # SCENARIOS
    # ========================================================

    @staticmethod
    def generate_scenarios() -> list[Scenario]:

        return [

            Scenario(
                name="Baseline"
            ),

            Scenario(
                name="Aggressive Growth",
                price_change_pct=5,
                demand_change_pct=15,
                marketing_change_pct=20,
                variable_cost_change_pct=-5,
            ),

            Scenario(
                name="Price Optimization",
                price_change_pct=10,
                demand_change_pct=5,
                variable_cost_change_pct=-2,
            ),

            Scenario(
                name="Demand Expansion",
                demand_change_pct=20,
                marketing_change_pct=15,
            ),

            Scenario(
                name="Marketing Expansion",
                marketing_change_pct=30,
            ),

            Scenario(
                name="Cost Reduction",
                variable_cost_change_pct=-15,
                fixed_cost_change_pct=-5,
            ),

            Scenario(
                name="Conservative Growth",
                price_change_pct=2,
                demand_change_pct=3,
                marketing_change_pct=5,
                variable_cost_change_pct=-2,
            ),

            Scenario(
                name="Downside",
                price_change_pct=-5,
                demand_change_pct=-10,
                marketing_change_pct=-10,
                variable_cost_change_pct=10,
                fixed_cost_change_pct=5,
            ),

            Scenario(
                name="Recession",
                price_change_pct=-8,
                demand_change_pct=-20,
                marketing_change_pct=-15,
                variable_cost_change_pct=12,
                fixed_cost_change_pct=8,
            ),
        ]

    # ========================================================
    # RANK
    # ========================================================

    @classmethod
    def rank(
        cls,
        revenue: float,
        profit: float,
        scenarios: list[Scenario],
    ) -> pd.DataFrame:

        rows = []

        for scenario in scenarios:

            try:

                rows.append(
                    cls.simulate(
                        revenue,
                        profit,
                        scenario,
                    )
                )

            except Exception as error:

                rows.append({

                    "name":
                        scenario.name,

                    "error":
                        str(error),

                    "decision_score":
                        -999,
                })

        if not rows:

            return pd.DataFrame()

        result = pd.DataFrame(
            rows
        )

        if "decision_score" in result:

            result = result.sort_values(
                "decision_score",
                ascending=False,
            )

        result = (
            result
            .reset_index(
                drop=True
            )
        )

        result.insert(
            0,
            "rank",
            range(
                1,
                len(result) + 1,
            ),
        )

        return result

    # ========================================================
    # SENSITIVITY
    # ========================================================

    @classmethod
    def sensitivity_analysis(
        cls,
        revenue: float,
        profit: float,
        variable: str = "price",
        values: list[float] | None = None,
    ) -> pd.DataFrame:

        if values is None:

            values = [
                -20,
                -15,
                -10,
                -5,
                0,
                5,
                10,
                15,
                20,
            ]

        rows = []

        mapping = {

            "price":
                "price_change_pct",

            "demand":
                "demand_change_pct",

            "marketing":
                "marketing_change_pct",

            "variable_cost":
                "variable_cost_change_pct",

            "fixed_cost":
                "fixed_cost_change_pct",
        }

        if variable not in mapping:

            raise ValueError(
                "Unsupported sensitivity variable."
            )

        field = mapping[
            variable
        ]

        for value in values:

            scenario = Scenario(
                name=f"{variable}_{value}"
            )

            setattr(
                scenario,
                field,
                value,
            )

            result = cls.simulate(
                revenue,
                profit,
                scenario,
            )

            rows.append({

                "change_pct":
                    value,

                "revenue":
                    result["revenue"],

                "profit":
                    result["profit"],

                "margin_pct":
                    result["margin_pct"],

                "profit_change_pct":
                    result["profit_change_pct"],

                "risk_score":
                    result["risk_score"],
            })

        return pd.DataFrame(
            rows
        )

    # ========================================================
    # BREAK EVEN
    # ========================================================

    @classmethod
    def break_even_price_change(
        cls,
        revenue: float,
        profit: float,
    ) -> float:

        if revenue <= 0:

            return 0.0

        candidates = np.linspace(
            -50,
            50,
            2001,
        )

        for change in candidates:

            scenario = Scenario(
                name="Break-even",
                price_change_pct=float(
                    change
                ),
            )

            result = cls.simulate(
                revenue,
                profit,
                scenario,
            )

            if (
                result["profit"]
                >= profit
            ):

                return round(
                    float(change),
                    2,
                )

        return 0.0

    # ========================================================
    # EXECUTIVE DECISION REPORT
    # ========================================================

    @classmethod
    def decision_report(
        cls,
        revenue: float,
        profit: float,
        scenarios: list[Scenario] | None = None,
    ) -> dict[str, Any]:

        if scenarios is None:

            scenarios = (
                cls.generate_scenarios()
            )

        ranking = cls.rank(
            revenue,
            profit,
            scenarios,
        )

        if ranking.empty:

            return {

                "status":
                    "unavailable",

                "ranking":
                    pd.DataFrame(),

                "best_scenario":
                    None,

                "worst_scenario":
                    None,

                "recommendation":
                    "No scenarios available.",
            }

        best = ranking.iloc[
            0
        ].to_dict()

        worst = ranking.iloc[
            -1
        ].to_dict()

        break_even = (
            cls.break_even_price_change(
                revenue,
                profit,
            )
        )

        if (
            best.get(
                "decision_score",
                -999,
            ) >= 10
        ):

            recommendation = (

                f"Prioritize "
                f"'{best.get('name')}'. "
                f"Expected profit impact is "
                f"{best.get('profit_change_pct', 0):.2f}% "
                f"with a risk score of "
                f"{best.get('risk_score', 0):.1f}/100."
            )

        elif (
            best.get(
                "decision_score",
                -999,
            ) >= 0
        ):

            recommendation = (

                f"'{best.get('name')}' is the strongest "
                f"available scenario, but the expected "
                f"benefit is limited."
            )

        else:

            recommendation = (

                "No tested scenario provides a "
                "sufficiently attractive "
                "risk-adjusted improvement."
            )

        return {

            "status":
                "success",

            "engine_version":
                cls.VERSION,

            "baseline": {

                "revenue":
                    round(
                        float(revenue),
                        2,
                    ),

                "profit":
                    round(
                        float(profit),
                        2,
                    ),

                "margin_pct":
                    round(
                        (
                            profit / revenue * 100
                        )
                        if revenue
                        else 0,
                        2,
                    ),
            },

            "scenario_count":
                len(ranking),

            "ranking":
                ranking,

            "best_scenario":
                best,

            "worst_scenario":
                worst,

            "break_even_price_change_pct":
                break_even,

            "average_profit_change_pct":
                round(
                    float(
                        ranking[
                            "profit_change_pct"
                        ].mean()
                    ),
                    2,
                ),

            "average_risk_score":
                round(
                    float(
                        ranking[
                            "risk_score"
                        ].mean()
                    ),
                    2,
                ),

            "recommendation":
                recommendation,
        }

    # ========================================================
    # MAIN GENERATE API
    # ========================================================

    @classmethod
    def generate(
        cls,
        df: pd.DataFrame,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        context = (
            context
            if isinstance(
                context,
                dict,
            )
            else {}
        )

        metrics = (
            cls.discover_business_metrics(
                df
            )
        )

        revenue = metrics[
            "TOTAL_REVENUE"
        ]

        profit = metrics[
            "TOTAL_PROFIT"
        ]

        # ----------------------------------------------------
        # Scenario intelligence
        # ----------------------------------------------------

        if revenue > 0:

            decision_report = (
                cls.decision_report(
                    revenue,
                    profit,
                )
            )

        else:

            decision_report = {

                "status":
                    "insufficient_business_metrics",

                "baseline":
                    metrics,

                "scenario_count":
                    0,

                "ranking":
                    pd.DataFrame(),

                "best_scenario":
                    None,

                "worst_scenario":
                    None,

                "break_even_price_change_pct":
                    0.0,

                "recommendation":
                    (
                        "NEXUS could not identify a "
                        "revenue metric required for "
                        "decision simulation."
                    ),
            }

        # ----------------------------------------------------
        # Dataset intelligence
        # ----------------------------------------------------

        health = context.get(
            "health",
            {},
        )

        risks = context.get(
            "risks",
            [],
        )

        quality = context.get(
            "quality",
            {},
        )

        risk_count = (
            len(risks)
            if isinstance(
                risks,
                list,
            )
            else 0
        )

        health_score = 0.0

        if isinstance(
            health,
            dict,
        ):

            health_score = cls._safe_float(
                health.get(
                    "score",
                    health.get(
                        "health_score",
                        0,
                    ),
                )
            )

        # ----------------------------------------------------
        # Overall confidence
        # ----------------------------------------------------

        confidence = 100.0

        if health_score:

            confidence *= (
                health_score / 100
            )

        confidence -= min(
            risk_count * 5,
            25,
        )

        confidence = max(
            min(
                confidence,
                100,
            ),
            0,
        )

        # ----------------------------------------------------
        # Final package
        # ----------------------------------------------------

        return {

            "engine":
                "NEXUS Decision Intelligence",

            "version":
                cls.VERSION,

            "status":
                decision_report.get(
                    "status",
                    "unknown",
                ),

            "business_metrics":
                metrics,

            "baseline":
                decision_report.get(
                    "baseline",
                    {},
                ),

            "scenario_count":
                decision_report.get(
                    "scenario_count",
                    0,
                ),

            "scenario_ranking":
                decision_report.get(
                    "ranking",
                    pd.DataFrame(),
                ),

            "best_scenario":
                decision_report.get(
                    "best_scenario",
                ),

            "worst_scenario":
                decision_report.get(
                    "worst_scenario",
                ),

            "break_even_price_change_pct":
                decision_report.get(
                    "break_even_price_change_pct",
                    0.0,
                ),

            "average_profit_change_pct":
                decision_report.get(
                    "average_profit_change_pct",
                    0.0,
                ),

            "average_risk_score":
                decision_report.get(
                    "average_risk_score",
                    0.0,
                ),

            "confidence_score":
                round(
                    confidence,
                    2,
                ),

            "data_health_score":
                health_score,

            "recommendation":
                decision_report.get(
                    "recommendation",
                    "",
                ),

            "quality_context":
                quality,

            "risk_context":
                risks,
        }