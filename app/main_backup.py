# ============================================================
# NEXUS AI
# Autonomous Enterprise Data Analyst
# Main Streamlit Application
# ============================================================

import sys
from pathlib import Path

# ------------------------------------------------------------
# PROJECT PATH FIX
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------

import io
import json
from datetime import datetime

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from app.services.data_loader import DataLoader

from app.agents.orchestrator import (
    AutonomousOrchestrator
)

from app.analytics.correlation import (
    CorrelationEngine
)

from app.analytics.anomaly import (
    AnomalyDetector
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="NEXUS AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #0e1117;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    .nexus-title {
        font-size: 3.2rem;
        font-weight: 800;
        letter-spacing: -2px;
        margin-bottom: 0;
    }

    .nexus-subtitle {
        font-size: 1.15rem;
        color: #9ca3af;
        margin-bottom: 2rem;
    }

    .section-title {
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }

    .status-card {
        padding: 1rem;
        border-radius: 12px;
        background: #161b22;
        border: 1px solid #30363d;
        margin-bottom: 1rem;
    }

    .insight-card {
        padding: 1rem 1.2rem;
        border-radius: 12px;
        background: #161b22;
        border-left: 4px solid #58a6ff;
        margin-bottom: 0.8rem;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

if "df" not in st.session_state:
    st.session_state.df = None

if "results" not in st.session_state:
    st.session_state.results = None

if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False

if "anomaly_results" not in st.session_state:
    st.session_state.anomaly_results = None


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="nexus-title">🤖 NEXUS AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="nexus-subtitle">
    Autonomous Enterprise Data Intelligence Platform
    </div>
    """,
    unsafe_allow_html=True
)


st.write(
    """
    Upload enterprise data and let NEXUS AI automatically
    profile, validate, clean, analyze and discover business insights.
    """
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("🧠 NEXUS CONTROL CENTER")

    st.markdown("---")

    st.markdown(
        """
        **Autonomous Intelligence Pipeline**

        🔹 Data Discovery  
        🔹 Schema Intelligence  
        🔹 Data Quality  
        🔹 Data Cleaning  
        🔹 Business KPI Detection  
        🔹 Exploratory Analysis  
        🔹 Statistical Analysis  
        🔹 Correlation Intelligence  
        🔹 Anomaly Detection  
        🔹 Business Insights  
        🔹 Decision Support  
        """
    )

    st.markdown("---")

    st.subheader("⚙️ System")

    st.write(
        f"Python: `{sys.version.split()[0]}`"
    )

    st.write(
        f"Analysis Engine: `NEXUS`"
    )

    st.write(
        f"Session: `{datetime.now().strftime('%Y-%m-%d %H:%M')}`"
    )


# ============================================================
# DATA UPLOAD
# ============================================================

st.markdown(
    '<div class="section-title">📂 Data Ingestion</div>',
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader(
    "Upload CSV / Excel / JSON / Parquet",
    type=[
        "csv",
        "xlsx",
        "xls",
        "json",
        "parquet"
    ]
)


# ============================================================
# DATA PROCESSING
# ============================================================

if uploaded_file:

    # --------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------

    try:

        df = DataLoader.load(
            uploaded_file
        )

        DataLoader.validate(df)

        st.session_state.df = df

    except Exception as error:

        st.error(
            f"❌ Dataset loading failed: {error}"
        )

        st.stop()


    # --------------------------------------------------------
    # Basic file information
    # --------------------------------------------------------

    file_size = uploaded_file.size

    info1, info2, info3, info4 = st.columns(4)

    info1.metric(
        "File",
        uploaded_file.name
    )

    info2.metric(
        "Size",
        f"{file_size / 1024:.1f} KB"
    )

    info3.metric(
        "Rows",
        f"{len(df):,}"
    )

    info4.metric(
        "Columns",
        f"{len(df.columns):,}"
    )


    # ========================================================
    # AUTONOMOUS ANALYSIS
    # ========================================================

    if st.button(
        "🚀 Run Full Autonomous Analysis",
        type="primary",
        use_container_width=True
    ):

        orchestrator = (
            AutonomousOrchestrator()
        )

        with st.status(
            "🧠 NEXUS AI is analyzing your dataset...",
            expanded=True
        ) as status:

            st.write("🔍 Discovering dataset structure...")

            st.write("🧹 Evaluating data quality...")

            st.write("🧠 Detecting business metrics...")

            st.write("📊 Running exploratory analysis...")

            st.write("🔗 Analyzing statistical relationships...")

            st.write("💡 Generating business insights...")

            try:

                results = (
                    orchestrator
                    .execute(df)
                )

                st.session_state.results = results
                st.session_state.analysis_complete = True

                status.update(
                    label="✅ Autonomous analysis completed",
                    state="complete",
                    expanded=False
                )

            except Exception as error:

                status.update(
                    label="❌ Analysis failed",
                    state="error"
                )

                st.error(
                    f"Autonomous analysis failed: {error}"
                )

                st.stop()


    # ========================================================
    # USE RESULTS
    # ========================================================

    results = st.session_state.results

    if results:

        cleaned_df = results.get(
            "cleaned_data",
            df
        )

        profile = results.get(
            "profile",
            {}
        )

        quality = results.get(
            "quality",
            []
        )

        kpis = results.get(
            "kpis",
            {}
        )

        insights = results.get(
            "insights",
            []
        )


        # ====================================================
        # EXECUTIVE SUMMARY
        # ====================================================

        st.divider()

        st.markdown(
            '<div class="section-title">🎯 Executive Intelligence</div>',
            unsafe_allow_html=True
        )

        total_rows = len(cleaned_df)

        total_columns = len(
            cleaned_df.columns
        )

        missing_values = int(
            cleaned_df.isna().sum().sum()
        )

        duplicate_rows = int(
            cleaned_df.duplicated().sum()
        )

        numeric_columns = (
            cleaned_df
            .select_dtypes(
                include="number"
            )
            .columns
            .tolist()
        )

        categorical_columns = (
            cleaned_df
            .select_dtypes(
                exclude="number"
            )
            .columns
            .tolist()
        )


        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "Rows",
            f"{total_rows:,}"
        )

        c2.metric(
            "Columns",
            f"{total_columns:,}"
        )

        c3.metric(
            "Numeric Fields",
            f"{len(numeric_columns):,}"
        )

        c4.metric(
            "Missing Values",
            f"{missing_values:,}"
        )

        c5.metric(
            "Duplicates",
            f"{duplicate_rows:,}"
        )


        # ====================================================
        # BUSINESS KPIs
        # ====================================================

        st.markdown(
            '<div class="section-title">💰 Business Intelligence</div>',
            unsafe_allow_html=True
        )


        if kpis:

            kpi_items = list(
                kpis.items()
            )

            # Show maximum 6 KPI cards
            kpi_items = kpi_items[:6]

            if kpi_items:

                columns = st.columns(
                    len(kpi_items)
                )

                for column, (
                    name,
                    value
                ) in zip(
                    columns,
                    kpi_items
                ):

                    formatted_name = (
                        str(name)
                        .replace("_", " ")
                        .title()
                    )

                    try:

                        if (
                            "MARGIN"
                            in str(name).upper()
                        ):

                            formatted_value = (
                                f"{float(value):.2f}%"
                            )

                        elif isinstance(
                            value,
                            (int, float)
                        ):

                            formatted_value = (
                                f"₹{value:,.2f}"
                            )

                        else:

                            formatted_value = str(
                                value
                            )

                    except Exception:

                        formatted_value = str(
                            value
                        )

                    column.metric(
                        formatted_name,
                        formatted_value
                    )

        else:

            st.info(
                "No automatic business KPIs detected."
            )


        # ====================================================
        # DATA INTELLIGENCE TABS
        # ====================================================

        st.divider()

        tabs = st.tabs(
            [
                "📋 Dataset",
                "🧹 Data Quality",
                "📈 EDA",
                "🔗 Relationships",
                "🚨 Anomalies",
                "🧠 AI Insights",
                "📤 Export"
            ]
        )


        # ====================================================
        # TAB 1 — DATASET
        # ====================================================

        with tabs[0]:

            st.subheader(
                "📋 Dataset Intelligence"
            )

            st.dataframe(
                cleaned_df,
                use_container_width=True,
                height=450
            )

            st.subheader(
                "🧬 Schema Intelligence"
            )

            schema_data = pd.DataFrame(
                {
                    "Column":
                        cleaned_df.columns,

                    "Data Type":
                        [
                            str(dtype)
                            for dtype
                            in cleaned_df.dtypes
                        ],

                    "Non-Null":
                        [
                            int(
                                cleaned_df[col]
                                .notna()
                                .sum()
                            )
                            for col
                            in cleaned_df.columns
                        ],

                    "Unique":
                        [
                            int(
                                cleaned_df[col]
                                .nunique()
                            )
                            for col
                            in cleaned_df.columns
                        ],

                    "Missing":
                        [
                            int(
                                cleaned_df[col]
                                .isna()
                                .sum()
                            )
                            for col
                            in cleaned_df.columns
                        ]
                }
            )

            st.dataframe(
                schema_data,
                use_container_width=True
            )


        # ====================================================
        # TAB 2 — DATA QUALITY
        # ====================================================

        with tabs[1]:

            st.subheader(
                "🧹 Data Quality Intelligence"
            )

            quality_missing = (
                cleaned_df
                .isna()
                .sum()
                .reset_index()
            )

            quality_missing.columns = [
                "Column",
                "Missing Values"
            ]

            quality_missing = (
                quality_missing
                .sort_values(
                    "Missing Values",
                    ascending=False
                )
            )

            st.dataframe(
                quality_missing,
                use_container_width=True
            )


            if quality:

                st.subheader(
                    "⚠️ Detected Quality Issues"
                )

                try:

                    st.dataframe(
                        pd.DataFrame(quality),
                        use_container_width=True
                    )

                except Exception:

                    st.write(quality)

            else:

                st.success(
                    "✅ No major data quality issues detected."
                )


        # ====================================================
        # TAB 3 — EDA
        # ====================================================

        with tabs[2]:

            st.subheader(
                "📈 Autonomous Exploratory Analysis"
            )


            if (
                numeric_columns
                and categorical_columns
            ):

                col1, col2 = st.columns(2)

                with col1:

                    dimension = st.selectbox(
                        "Business Dimension",
                        categorical_columns,
                        key="eda_dimension"
                    )

                with col2:

                    metric = st.selectbox(
                        "Business Metric",
                        numeric_columns,
                        key="eda_metric"
                    )


                grouped = (
                    cleaned_df
                    .groupby(dimension)[metric]
                    .sum()
                    .sort_values(
                        ascending=False
                    )
                    .reset_index()
                )


                figure = px.bar(
                    grouped,
                    x=dimension,
                    y=metric,
                    title=(
                        f"{metric} by {dimension}"
                    ),
                    text_auto=True
                )


                figure.update_layout(
                    template="plotly_dark"
                )


                st.plotly_chart(
                    figure,
                    use_container_width=True
                )


                # ------------------------------------------------
                # Distribution
                # ------------------------------------------------

                st.subheader(
                    f"📊 Distribution of {metric}"
                )

                histogram = px.histogram(
                    cleaned_df,
                    x=metric,
                    marginal="box",
                    title=f"{metric} Distribution"
                )

                histogram.update_layout(
                    template="plotly_dark"
                )

                st.plotly_chart(
                    histogram,
                    use_container_width=True
                )


            elif numeric_columns:

                metric = st.selectbox(
                    "Select metric",
                    numeric_columns,
                    key="numeric_only_metric"
                )

                histogram = px.histogram(
                    cleaned_df,
                    x=metric,
                    marginal="box"
                )

                histogram.update_layout(
                    template="plotly_dark"
                )

                st.plotly_chart(
                    histogram,
                    use_container_width=True
                )

            else:

                st.warning(
                    "No numeric fields available for EDA."
                )


            # ------------------------------------------------
            # Date Trend Detection
            # ------------------------------------------------

            date_columns = []

            for column in cleaned_df.columns:

                try:

                    converted = pd.to_datetime(
                        cleaned_df[column],
                        errors="coerce"
                    )

                    if (
                        converted.notna().mean()
                        > 0.8
                    ):

                        date_columns.append(
                            column
                        )

                except Exception:
                    pass


            if (
                date_columns
                and numeric_columns
            ):

                st.subheader(
                    "📅 Temporal Intelligence"
                )

                trend_date = st.selectbox(
                    "Date Column",
                    date_columns,
                    key="trend_date"
                )

                trend_metric = st.selectbox(
                    "Metric",
                    numeric_columns,
                    key="trend_metric"
                )


                trend_df = cleaned_df.copy()

                trend_df["_NEXUS_DATE"] = (
                    pd.to_datetime(
                        trend_df[trend_date],
                        errors="coerce"
                    )
                )

                trend_df = (
                    trend_df
                    .dropna(
                        subset=["_NEXUS_DATE"]
                    )
                    .groupby(
                        "_NEXUS_DATE"
                    )[trend_metric]
                    .sum()
                    .reset_index()
                )


                trend_figure = px.line(
                    trend_df,
                    x="_NEXUS_DATE",
                    y=trend_metric,
                    markers=True,
                    title=(
                        f"{trend_metric} Trend"
                    )
                )

                trend_figure.update_layout(
                    template="plotly_dark"
                )

                st.plotly_chart(
                    trend_figure,
                    use_container_width=True
                )


        # ====================================================
        # TAB 4 — RELATIONSHIPS
        # ====================================================

        with tabs[3]:

            st.subheader(
                "🔗 Relationship Intelligence"
            )

            correlation_engine = (
                CorrelationEngine()
            )

            try:

                correlation = (
                    correlation_engine
                    .calculate(cleaned_df)
                )

                if correlation is not None:

                    st.dataframe(
                        correlation,
                        use_container_width=True
                    )

                    # --------------------------------------------
                    # Correlation Heatmap
                    # --------------------------------------------

                    if len(numeric_columns) >= 2:

                        corr_matrix = (
                            cleaned_df[
                                numeric_columns
                            ]
                            .corr()
                        )

                        heatmap = go.Figure(
                            data=go.Heatmap(
                                z=corr_matrix.values,
                                x=corr_matrix.columns,
                                y=corr_matrix.columns,
                                text=corr_matrix.round(2).values,
                                texttemplate="%{text}",
                                colorscale="RdBu",
                                zmin=-1,
                                zmax=1
                            )
                        )

                        heatmap.update_layout(
                            title="Correlation Heatmap",
                            template="plotly_dark"
                        )

                        st.plotly_chart(
                            heatmap,
                            use_container_width=True
                        )

                else:

                    st.info(
                        "Not enough numeric data for correlation analysis."
                    )

            except Exception as error:

                st.warning(
                    f"Correlation analysis unavailable: {error}"
                )


        # ====================================================
        # TAB 5 — ANOMALIES
        # ====================================================

        with tabs[4]:

            st.subheader(
                "🚨 Anomaly Intelligence"
            )

            if numeric_columns:

                anomaly_column = st.selectbox(
                    "Select metric to investigate",
                    numeric_columns,
                    key="anomaly_metric"
                )


                if st.button(
                    "🔍 Run Anomaly Investigation",
                    key="anomaly_button"
                ):

                    try:

                        detector = (
                            AnomalyDetector()
                        )

                        anomaly_data = (
                            detector.detect(
                                cleaned_df,
                                anomaly_column
                            )
                        )

                        st.session_state.anomaly_results = (
                            anomaly_data
                        )

                    except Exception as error:

                        st.error(
                            f"Anomaly detection failed: {error}"
                        )


                anomaly_data = (
                    st.session_state.anomaly_results
                )


                if anomaly_data is not None:

                    anomaly_count = int(
                        anomaly_data[
                            "anomaly"
                        ].sum()
                    )


                    if anomaly_count:

                        st.warning(
                            f"🚨 {anomaly_count} "
                            f"potential anomalies detected."
                        )

                        anomaly_rows = (
                            anomaly_data[
                                anomaly_data["anomaly"]
                            ]
                        )

                        st.dataframe(
                            anomaly_rows,
                            use_container_width=True
                        )

                    else:

                        st.success(
                            "✅ No significant anomalies detected."
                        )

            else:

                st.info(
                    "No numeric columns available."
                )


        # ====================================================
        # TAB 6 — AI INSIGHTS
        # ====================================================

        with tabs[5]:

            st.subheader(
                "🧠 Autonomous AI Findings"
            )


            if insights:

                for index, insight in enumerate(
                    insights,
                    start=1
                ):

                    st.markdown(
                        f"""
                        <div class="insight-card">
                        <strong>Finding {index}</strong><br>
                        {insight}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            else:

                st.info(
                    "NEXUS did not generate additional findings."
                )


            # ------------------------------------------------
            # Automatic statistical observations
            # ------------------------------------------------

            st.subheader(
                "🔬 Statistical Observations"
            )


            if numeric_columns:

                stats = cleaned_df[
                    numeric_columns
                ].describe().T

                stats[
                    "coefficient_of_variation"
                ] = (
                    stats["std"]
                    / stats["mean"].replace(
                        0,
                        pd.NA
                    )
                )

                st.dataframe(
                    stats.round(3),
                    use_container_width=True
                )


        # ====================================================
        # TAB 7 — EXPORT
        # ====================================================

        with tabs[6]:

            st.subheader(
                "📤 Intelligence Export Center"
            )


            # ------------------------------------------------
            # Cleaned CSV
            # ------------------------------------------------

            csv_data = cleaned_df.to_csv(
                index=False
            ).encode("utf-8")


            st.download_button(
                "⬇️ Download Cleaned Dataset",
                data=csv_data,
                file_name="nexus_cleaned_dataset.csv",
                mime="text/csv",
                use_container_width=True
            )


            # ------------------------------------------------
            # JSON Summary
            # ------------------------------------------------

            report = {
                "generated_at":
                    datetime.now().isoformat(),

                "dataset": {
                    "rows":
                        len(cleaned_df),

                    "columns":
                        len(cleaned_df.columns),

                    "missing_values":
                        int(
                            cleaned_df
                            .isna()
                            .sum()
                            .sum()
                        ),

                    "duplicate_rows":
                        int(
                            cleaned_df
                            .duplicated()
                            .sum()
                        )
                },

                "kpis":
                    kpis,

                "insights":
                    insights
            }


            report_json = json.dumps(
                report,
                indent=4,
                default=str
            )


            st.download_button(
                "⬇️ Download AI Analysis Report",
                data=report_json,
                file_name="nexus_ai_report.json",
                mime="application/json",
                use_container_width=True
            )


        # ====================================================
        # ASK NEXUS
        # ====================================================

        st.divider()

        st.markdown(
            '<div class="section-title">💬 Ask NEXUS AI</div>',
            unsafe_allow_html=True
        )

        st.write(
            "Ask questions about the uploaded dataset."
        )


        question = st.text_area(
            "Your question",
            placeholder=(
                "Example: Which product generated "
                "the highest sales?"
            ),
            key="nexus_question"
        )


        if st.button(
            "🧠 Analyze Question",
            key="question_button"
        ):

            if question.strip():

                question_lower = (
                    question.lower()
                )


                # --------------------------------------------
                # Simple autonomous analytical reasoning
                # --------------------------------------------

                answered = False


                # Highest / maximum
                if (
                    "highest" in question_lower
                    or "maximum" in question_lower
                    or "max" in question_lower
                ):

                    for column in numeric_columns:

                        if column.lower() in question_lower:

                            row = cleaned_df.loc[
                                cleaned_df[column].idxmax()
                            ]

                            st.success(
                                f"Highest **{column}** "
                                f"is **{row[column]}**."
                            )

                            st.dataframe(
                                pd.DataFrame(
                                    [row]
                                ),
                                use_container_width=True
                            )

                            answered = True
                            break


                # Lowest / minimum
                if not answered and (
                    "lowest" in question_lower
                    or "minimum" in question_lower
                    or "min" in question_lower
                ):

                    for column in numeric_columns:

                        if column.lower() in question_lower:

                            row = cleaned_df.loc[
                                cleaned_df[column].idxmin()
                            ]

                            st.success(
                                f"Lowest **{column}** "
                                f"is **{row[column]}**."
                            )

                            st.dataframe(
                                pd.DataFrame(
                                    [row]
                                ),
                                use_container_width=True
                            )

                            answered = True
                            break


                # Average
                if not answered and (
                    "average" in question_lower
                    or "mean" in question_lower
                ):

                    found_metric = False

                    for column in numeric_columns:

                        if column.lower() in question_lower:

                            average = (
                                cleaned_df[column]
                                .mean()
                            )

                            st.info(
                                f"Average **{column}** "
                                f"is **{average:,.2f}**."
                            )

                            answered = True
                            found_metric = True
                            break


                # Count rows
                if not answered and (
                    "how many rows"
                    in question_lower
                    or "number of rows"
                    in question_lower
                ):

                    st.info(
                        f"The dataset contains "
                        f"**{len(cleaned_df):,} rows**."
                    )

                    answered = True


                if not answered:

                    st.info(
                        """
                        NEXUS has not yet mapped this question
                        to a deterministic analytical operation.

                        Use the generated insights, KPI cards,
                        EDA and relationship analysis above.
                        """
                    )

            else:

                st.warning(
                    "Please enter a question."
                )


else:

    # ========================================================
    # LANDING PAGE
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-title">🚀 NEXUS Intelligence Pipeline</div>',
        unsafe_allow_html=True
    )

    pipeline_columns = st.columns(5)

    pipeline = [
        ("01", "📂", "Ingest"),
        ("02", "🧹", "Clean"),
        ("03", "📊", "Analyze"),
        ("04", "🧠", "Reason"),
        ("05", "🎯", "Decide")
    ]

    for column, (
        number,
        icon,
        title
    ) in zip(
        pipeline_columns,
        pipeline
    ):

        with column:

            st.markdown(
                f"""
                <div class="status-card">
                    <h3>{icon} {number}</h3>
                    <strong>{title}</strong>
                </div>
                """,
                unsafe_allow_html=True
            )


    st.info(
        """
        📂 Upload a business dataset above to activate
        the NEXUS autonomous intelligence engine.
        """
    )