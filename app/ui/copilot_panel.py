from __future__ import annotations

import pandas as pd
import streamlit as st

from app.agents.copilot_agent import CopilotAgent


class CopilotPanel:
    """
    Streamlit UI for the NEXUS AI Executive Copilot.
    """

    @staticmethod
    def render(
        dataframe: pd.DataFrame | None,
        results: dict | None
    ):

        st.header(
            "🤖 NEXUS Executive Copilot"
        )

        st.caption(
            "Ask questions about your business data "
            "using the intelligence already discovered "
            "by NEXUS."
        )

        if (
            dataframe is None
            or dataframe.empty
        ):

            st.info(
                "Upload a dataset to activate "
                "the Executive Copilot."
            )

            return

        results = results or {}

        # =====================================================
        # EXAMPLE QUESTIONS
        # =====================================================

        st.markdown(
            "### 💬 Ask NEXUS"
        )

        example_questions = [

            "Give me an executive summary",

            "What is the total revenue?",

            "What is the total profit?",

            "Which region is performing best?",

            "Which region is performing worst?",

            "What are the strongest correlations?",

            "Are there any anomalies?",

            "What are the biggest data quality issues?",

            "Why is performance changing?",

            "What should management focus on?"
        ]

        selected_example = st.selectbox(
            "Example questions",
            [
                "Choose a question..."
            ] + example_questions,
            key="copilot_example"
        )

        question = st.text_input(
            "Ask your own question",
            value=(
                ""
                if selected_example
                == "Choose a question..."
                else selected_example
            ),
            placeholder=(
                "Example: Why is profit low?"
            ),
            key="copilot_question"
        )

        ask = st.button(
            "🧠 Ask NEXUS",
            type="primary",
            width="stretch"
        )

        if ask:

            if not question.strip():

                st.warning(
                    "Please enter a question."
                )

                return

            with st.spinner(
                "NEXUS is analyzing your question..."
            ):

                agent = CopilotAgent(
                    dataframe=dataframe,
                    results=results
                )

                response = agent.ask(
                    question
                )

            # =================================================
            # RESPONSE
            # =================================================

            st.divider()

            st.markdown(
                "### 🧠 NEXUS Answer"
            )

            st.success(
                response.get(
                    "answer",
                    "No answer generated."
                )
            )

            intent = response.get(
                "intent"
            )

            if intent:

                st.caption(
                    f"Analysis type: `{intent}`"
                )

            findings = response.get(
                "findings",
                []
            )

            if findings:

                st.markdown(
                    "### 🔎 Supporting Findings"
                )

                for index, finding in enumerate(
                    findings,
                    start=1
                ):

                    st.write(
                        f"**{index}.** {finding}"
                    )

            st.caption(
                response.get(
                    "source",
                    "NEXUS"
                )
            )

        # =====================================================
        # QUICK ACTIONS
        # =====================================================

        st.divider()

        st.markdown(
            "### ⚡ Quick Analysis"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            if st.button(
                "📊 Executive Summary",
                width="stretch"
            ):

                agent = CopilotAgent(
                    dataframe=dataframe,
                    results=results
                )

                response = (
                    agent
                    .executive_summary()
                )

                st.info(
                    response["answer"]
                )

        with col2:

            if st.button(
                "🚨 Check Anomalies",
                width="stretch"
            ):

                agent = CopilotAgent(
                    dataframe=dataframe,
                    results=results
                )

                response = agent.ask(
                    "Are there any anomalies?"
                )

                st.warning(
                    response["answer"]
                )

        with col3:

            if st.button(
                "🎯 Recommendations",
                width="stretch"
            ):

                agent = CopilotAgent(
                    dataframe=dataframe,
                    results=results
                )

                response = agent.ask(
                    "What should management focus on?"
                )

                st.info(
                    response["answer"]
                )