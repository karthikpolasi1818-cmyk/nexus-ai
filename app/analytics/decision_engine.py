from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import numpy as np
import pandas as pd


# ============================================================
# SCENARIO MODEL
# ============================================================

@dataclass
class Scenario:
    name: str

    price_change_pct: float = 0.0
    demand_change_pct: float = 0.0
    marketing_change_pct: float = 0.0
    variable_cost_change_pct: float = 0.0
    fixed_cost_change_pct: float = 0.0

    # Advanced assumptions
    demand_elasticity: float = -0.30
    marketing_roi: float = 0.25

    # Risk assumptions
    uncertainty_pct: float = 5.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# DECISION ENGINE
# ============================================================

class DecisionEngine:

    VERSION = "2.0.0"

    # --------------------------------------------------------
    # SAFE NUMBER
    # --------------------------------------------------------

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            value = float(value)

            if not np.isfinite(value):
                return default

            return value

        except (TypeError, ValueError):
            return default

    # --------------------------------------------------------
    # SIMULATE
    # --------------------------------------------------------

    @staticmethod
    def simulate(
        revenue: float,
        profit: float,
        scenario: Scenario,
    ) -> dict[str, Any]:

        revenue = DecisionEngine._safe_float(revenue)
        profit = DecisionEngine._safe_float(profit)

        if revenue <= 0:
            raise ValueError(
                "Revenue must be greater than zero."
            )

        # ====================================================
        # BASE ECONOMICS
        # ====================================================

        base_margin = profit / revenue

        # Keep calculations stable even for unusual datasets.
        base_margin = max(
            min(base_margin, 1.0),
            -1.0,
        )

        variable_cost = max(
            revenue - profit,
            0.0,
        )

        fixed_cost = max(
            revenue - variable_cost - profit,
            0.0,
        )

        # ====================================================
        # PRICE IMPACT
        # ====================================================

        price_factor = (
            1.0
            + scenario.price_change_pct / 100.0
        )

        price_factor = max(
            price_factor,
            0.0,
        )

        # ====================================================
        # DEMAND IMPACT
        # ====================================================

        elasticity_effect = (
            scenario.demand_elasticity
            *
            scenario.price_change_pct
            / 100.0
        )

        demand_factor = (
            1.0
            + scenario.demand_change_pct / 100.0
            + elasticity_effect
        )

        demand_factor = max(
            demand_factor,
            0.0,
        )

        # ====================================================
        # MARKETING IMPACT
        # ====================================================

        marketing_factor = (
            1.0
            +
            (
                scenario.marketing_change_pct
                / 100.0
            )
            *
            scenario.marketing_roi
        )

        marketing_factor = max(
            marketing_factor,
            0.0,
        )

        # ====================================================
        # REVENUE
        # ====================================================

        revenue_factor = (
            price_factor
            *
            demand_factor
            *
            marketing_factor
        )

        new_revenue = (
            revenue
            *
            revenue_factor
        )

        # ====================================================
        # COST MODEL
        # ====================================================

        variable_cost_factor = (
            1.0
            +
            scenario.variable_cost_change_pct
            / 100.0
        )

        variable_cost_factor = max(
            variable_cost_factor,
            0.0,
        )

        new_variable_cost = (
            variable_cost
            *
            variable_cost_factor
            *
            demand_factor
            *
            marketing_factor
        )

        fixed_cost_factor = (
            1.0
            +
            scenario.fixed_cost_change_pct
            / 100.0
        )

        fixed_cost_factor = max(
            fixed_cost_factor,
            0.0,
        )

        new_fixed_cost = (
            fixed_cost
            *
            fixed_cost_factor
        )

        # ====================================================
        # PROFIT
        # ====================================================

        new_profit = (
            new_revenue
            -
            new_variable_cost
            -
            new_fixed_cost
        )

        # ====================================================
        # CHANGE METRICS
        # ====================================================

        revenue_change_pct = (
            (
                new_revenue / revenue
                - 1.0
            )
            * 100.0
        )

        profit_change_pct = (
            (
                new_profit / profit
                - 1.0
            )
            * 100.0
            if profit != 0
            else 0.0
        )

        projected_margin = (
            new_profit / new_revenue * 100.0
            if new_revenue
            else 0.0
        )

        margin_change = (
            projected_margin
            -
            base_margin * 100.0
        )

        profit_delta = (
            new_profit - profit
        )

        revenue_delta = (
            new_revenue - revenue
        )

        # ====================================================
        # BREAK-EVEN / RISK
        # ====================================================

        downside_revenue = (
            new_revenue
            *
            (
                1.0
                -
                scenario.uncertainty_pct / 100.0
            )
        )

        upside_revenue = (
            new_revenue
            *
            (
                1.0
                +
                scenario.uncertainty_pct / 100.0
            )
        )

        downside_profit = (
            new_profit
            *
            (
                1.0
                -
                scenario.uncertainty_pct / 100.0
            )
        )

        upside_profit = (
            new_profit
            *
            (
                1.0
                +
                scenario.uncertainty_pct / 100.0
            )
        )

        # ====================================================
        # DECISION SCORE
        # ====================================================

        decision_score = (
            profit_change_pct * 0.70
            +
            revenue_change_pct * 0.20
            +
            margin_change * 0.10
        )

        # ====================================================
        # DECISION CLASSIFICATION
        # ====================================================

        if decision_score >= 10:
            decision = "STRONGLY_RECOMMENDED"
            decision_label = "🟢 Strongly Recommended"

        elif decision_score >= 3:
            decision = "RECOMMENDED"
            decision_label = "🟢 Recommended"

        elif decision_score >= -3:
            decision = "NEUTRAL"
            decision_label = "🟡 Neutral"

        elif decision_score >= -10:
            decision = "CAUTION"
            decision_label = "🟠 Use Caution"

        else:
            decision = "NOT_RECOMMENDED"
            decision_label = "🔴 Not Recommended"

        # ====================================================
        # RETURN
        # ====================================================

        return {
            **scenario.to_dict(),

            "engine_version":
                DecisionEngine.VERSION,

            "base_revenue":
                round(revenue, 2),

            "base_profit":
                round(profit, 2),

            "base_margin_pct":
                round(
                    base_margin * 100.0,
                    2,
                ),

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

            "projected_margin_pct":
                round(
                    projected_margin,
                    2,
                ),

            "revenue_delta":
                round(
                    revenue_delta,
                    2,
                ),

            "profit_delta":
                round(
                    profit_delta,
                    2,
                ),

            "revenue_change_pct":
                round(
                    revenue_change_pct,
                    2,
                ),

            "profit_change_pct":
                round(
                    profit_change_pct,
                    2,
                ),

            "margin_change_pct":
                round(
                    margin_change,
                    2,
                ),

            "variable_cost":
                round(
                    new_variable_cost,
                    2,
                ),

            "fixed_cost":
                round(
                    new_fixed_cost,
                    2,
                ),

            "downside_revenue":
                round(
                    downside_revenue,
                    2,
                ),

            "upside_revenue":
                round(
                    upside_revenue,
                    2,
                ),

            "downside_profit":
                round(
                    downside_profit,
                    2,
                ),

            "upside_profit":
                round(
                    upside_profit,
                    2,
                ),

            "decision_score":
                round(
                    decision_score,
                    2,
                ),

            "decision":
                decision,

            "decision_label":
                decision_label,
        }

    # --------------------------------------------------------
    # RANK SCENARIOS
    # --------------------------------------------------------

    @staticmethod
    def rank(
        revenue: float,
        profit: float,
        scenarios: list[Scenario],
    ) -> pd.DataFrame:

        results = []

        for scenario in scenarios:

            try:

                result = (
                    DecisionEngine
                    .simulate(
                        revenue,
                        profit,
                        scenario,
                    )
                )

                results.append(result)

            except Exception as error:

                results.append(
                    {
                        "name":
                            scenario.name,

                        "decision":
                            "ERROR",

                        "error":
                            str(error),

                        "decision_score":
                            -999999,
                    }
                )

        result_df = pd.DataFrame(
            results
        )

        if result_df.empty:
            return result_df

        if "decision_score" in result_df.columns:

            result_df = (
                result_df
                .sort_values(
                    "decision_score",
                    ascending=False,
                )
                .reset_index(
                    drop=True
                )
            )

        return result_df

    # --------------------------------------------------------
    # GENERATE STANDARD SCENARIOS
    # --------------------------------------------------------

    @staticmethod
    def standard_scenarios() -> list[Scenario]:

        return [

            Scenario(
                name="Baseline"
            ),

            Scenario(
                name="Price Increase",
                price_change_pct=10,
            ),

            Scenario(
                name="Demand Growth",
                demand_change_pct=15,
            ),

            Scenario(
                name="Marketing Expansion",
                marketing_change_pct=50,
            ),

            Scenario(
                name="Cost Reduction",
                variable_cost_change_pct=-10,
                fixed_cost_change_pct=-5,
            ),

            Scenario(
                name="Aggressive Growth",
                price_change_pct=5,
                demand_change_pct=20,
                marketing_change_pct=50,
            ),

            Scenario(
                name="Cost Pressure",
                variable_cost_change_pct=15,
                fixed_cost_change_pct=10,
            ),

            Scenario(
                name="Economic Downturn",
                demand_change_pct=-20,
                marketing_change_pct=-20,
            ),
        ]

    # --------------------------------------------------------
    # SCENARIO MATRIX
    # --------------------------------------------------------

    @staticmethod
    def scenario_matrix(
        revenue: float,
        profit: float,
    ) -> pd.DataFrame:

        scenarios = (
            DecisionEngine
            .standard_scenarios()
        )

        return (
            DecisionEngine
            .rank(
                revenue,
                profit,
                scenarios,
            )
        )

    # --------------------------------------------------------
    # SENSITIVITY ANALYSIS
    # --------------------------------------------------------

    @staticmethod
    def sensitivity_analysis(
        revenue: float,
        profit: float,
        price_range=None,
        demand_range=None,
    ) -> pd.DataFrame:

        if price_range is None:
            price_range = np.arange(
                -20,
                21,
                5,
            )

        if demand_range is None:
            demand_range = np.arange(
                -20,
                21,
                5,
            )

        rows = []

        for price in price_range:

            for demand in demand_range:

                scenario = Scenario(
                    name="Sensitivity",
                    price_change_pct=float(price),
                    demand_change_pct=float(
                        demand
                    ),
                )

                result = (
                    DecisionEngine
                    .simulate(
                        revenue,
                        profit,
                        scenario,
                    )
                )

                rows.append(
                    {
                        "price_change_pct":
                            price,

                        "demand_change_pct":
                            demand,

                        "revenue":
                            result["revenue"],

                        "profit":
                            result["profit"],

                        "profit_change_pct":
                            result[
                                "profit_change_pct"
                            ],

                        "decision_score":
                            result[
                                "decision_score"
                            ],
                    }
                )

        return pd.DataFrame(rows)

    # --------------------------------------------------------
    # RECOMMENDATION
    # --------------------------------------------------------

    @staticmethod
    def recommendation(
        simulation: dict[str, Any],
    ) -> str:

        decision = simulation.get(
            "decision"
        )

        if decision == "STRONGLY_RECOMMENDED":

            return (
                "NEXUS strongly recommends "
                "this scenario because the "
                "projected financial outcome "
                "improves materially."
            )

        if decision == "RECOMMENDED":

            return (
                "NEXUS recommends this scenario "
                "based on the projected improvement "
                "in revenue, profit and margin."
            )

        if decision == "NEUTRAL":

            return (
                "NEXUS considers this scenario "
                "financially neutral. Additional "
                "business factors should be evaluated."
            )

        if decision == "CAUTION":

            return (
                "NEXUS recommends caution because "
                "the projected financial improvement "
                "is weak or negative."
            )

        return (
            "NEXUS does not recommend this scenario "
            "under the current assumptions."
        )