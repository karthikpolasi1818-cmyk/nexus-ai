from __future__ import annotations

import pandas as pd
import pytest


# ============================================================
# TEST DATA
# ============================================================

@pytest.fixture
def sample_dataframe():

    return pd.DataFrame(
        {
            "Sales": [
                100,
                200,
                150,
                1000,
                180,
            ],
            "Profit": [
                20,
                40,
                30,
                300,
                35,
            ],
            "Quantity": [
                2,
                4,
                3,
                20,
                4,
            ],
            "Region": [
                "South",
                "North",
                "South",
                "East",
                "North",
            ],
        }
    )


# ============================================================
# BASIC DATA TEST
# ============================================================

def test_dataframe_loads(
    sample_dataframe,
):

    assert isinstance(
        sample_dataframe,
        pd.DataFrame,
    )

    assert len(
        sample_dataframe
    ) == 5

    assert len(
        sample_dataframe.columns
    ) == 4


# ============================================================
# NUMERIC COLUMN TEST
# ============================================================

def test_numeric_columns(
    sample_dataframe,
):

    numeric_columns = (
        sample_dataframe
        .select_dtypes(
            include="number"
        )
        .columns
        .tolist()
    )

    assert "Sales" in numeric_columns
    assert "Profit" in numeric_columns
    assert "Quantity" in numeric_columns


# ============================================================
# INSIGHT ENGINE TEST
# ============================================================

def test_insight_engine(
    sample_dataframe,
):

    from app.analytics.insight_engine import (
        InsightEngine,
    )

    results = InsightEngine.generate(
        sample_dataframe
    )

    assert isinstance(
        results,
        dict,
    )

    assert "overall_status" in results
    assert "total_insights" in results

    assert isinstance(
        results["total_insights"],
        int,
    )

    assert results["total_insights"] >= 0


# ============================================================
# ORCHESTRATOR TEST
# ============================================================

def test_orchestrator(
    sample_dataframe,
):

    from app.agents.advanced_orchestrator import (
        AdvancedNexusOrchestrator,
    )

    orchestrator = (
        AdvancedNexusOrchestrator()
    )

    results = orchestrator.execute(
        sample_dataframe,
        target="Sales",
    )

    assert isinstance(
        results,
        dict,
    )

    assert len(
        results
    ) > 0


# ============================================================
# DECISION ENGINE TEST
# ============================================================

def test_decision_engine(
    sample_dataframe,
):

    from app.analytics.decision_engine import (
        DecisionEngine,
        Scenario,
    )

    revenue = float(
        sample_dataframe[
            "Sales"
        ].sum()
    )

    profit = float(
        sample_dataframe[
            "Profit"
        ].sum()
    )

    scenario = Scenario(
        name="Test Scenario",
        price_change_pct=5,
        demand_change_pct=0,
        marketing_change_pct=10,
        variable_cost_change_pct=0,
        fixed_cost_change_pct=0,
    )

    result = DecisionEngine.simulate(
        revenue,
        profit,
        scenario,
    )

    assert isinstance(
        result,
        dict,
    )

    assert "revenue" in result
    assert "profit" in result
    assert "revenue_change_pct" in result
    assert "profit_change_pct" in result


# ============================================================
# REPORT GENERATOR TEST
# ============================================================

def test_report_generator(
    sample_dataframe,
):

    from app.agents.advanced_orchestrator import (
        AdvancedNexusOrchestrator,
    )

    from app.services.report_generator import (
        generate_report,
    )

    orchestrator = (
        AdvancedNexusOrchestrator()
    )

    results = orchestrator.execute(
        sample_dataframe,
        target="Sales",
    )

    pdf = generate_report(
        results,
        sample_dataframe,
    )

    assert isinstance(
        pdf,
        (
            bytes,
            bytearray,
        ),
    )

    assert len(
        pdf
    ) > 100


# ============================================================
# JSON SERIALIZATION TEST
# ============================================================

def test_results_are_json_serializable(
    sample_dataframe,
):

    import json

    from app.agents.advanced_orchestrator import (
        AdvancedNexusOrchestrator,
    )

    from app.ui.advanced_panels import (
        AdvancedPanels,
    )

    orchestrator = (
        AdvancedNexusOrchestrator()
    )

    results = orchestrator.execute(
        sample_dataframe,
        target="Sales",
    )

    cleaned = (
        AdvancedPanels._json_safe(
            results
        )
    )

    serialized = json.dumps(
        cleaned,
        default=str,
    )

    assert isinstance(
        serialized,
        str,
    )

    assert len(
        serialized
    ) > 0


# ============================================================
# NO EMPTY DATA TEST
# ============================================================

def test_empty_dataframe_handling():

    from app.analytics.insight_engine import (
        InsightEngine,
    )

    dataframe = pd.DataFrame()

    try:

        results = InsightEngine.generate(
            dataframe
        )

        assert isinstance(
            results,
            dict,
        )

    except (
        ValueError,
        KeyError,
        TypeError,
    ):

        # Acceptable if the engine
        # explicitly rejects empty data.
        assert True