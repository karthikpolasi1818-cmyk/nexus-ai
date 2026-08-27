from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


class NexusReportGenerator:
    """
    Production-safe PDF report generator for NEXUS AI.

    Handles:
    - dictionaries
    - lists
    - DataFrames
    - Pandas/NumPy scalar values
    - missing analysis sections
    - nested result structures
    """

    # =========================================================
    # SAFE VALUE HELPERS
    # =========================================================

    @staticmethod
    def _safe(value: Any) -> Any:

        if value is None:
            return None

        try:
            result = pd.isna(value)

            if isinstance(result, bool) and result:
                return None

        except (TypeError, ValueError):
            pass

        if hasattr(value, "item"):

            try:
                return value.item()

            except Exception:
                pass

        return value

    @staticmethod
    def _text(
        value: Any,
        default: str = "N/A",
    ) -> str:

        value = NexusReportGenerator._safe(value)

        if value is None:
            return default

        if isinstance(value, dict):

            parts = []

            for key, item in value.items():

                parts.append(
                    f"{key}: "
                    f"{NexusReportGenerator._text(item)}"
                )

            return "; ".join(parts)

        if isinstance(
            value,
            (list, tuple, set),
        ):

            return ", ".join(
                NexusReportGenerator._text(item)
                for item in value
            )

        return str(value)

    @staticmethod
    def _get(
        results: dict[str, Any] | None,
        key: str,
        default: Any = None,
    ) -> Any:

        if not isinstance(results, dict):
            return default

        return results.get(
            key,
            default,
        )

    # =========================================================
    # PDF CALLBACK
    # =========================================================

    @staticmethod
    def _add_page_number(
        canvas,
        document,
    ):

        canvas.saveState()

        canvas.setFont(
            "Helvetica",
            8,
        )

        canvas.drawCentredString(
            A4[0] / 2,
            10 * mm,
            f"NEXUS AI - Page {document.page}",
        )

        canvas.restoreState()

    # =========================================================
    # STYLES
    # =========================================================

    @staticmethod
    def _create_styles():

        base = getSampleStyleSheet()

        return {

            "title": ParagraphStyle(
                "NexusTitle",
                parent=base["Title"],
                alignment=TA_CENTER,
                fontSize=22,
                leading=27,
                spaceAfter=12,
            ),

            "subtitle": ParagraphStyle(
                "NexusSubtitle",
                parent=base["Normal"],
                alignment=TA_CENTER,
                fontSize=10,
                textColor=colors.grey,
                spaceAfter=18,
            ),

            "heading": ParagraphStyle(
                "NexusHeading",
                parent=base["Heading2"],
                fontSize=15,
                leading=19,
                spaceBefore=12,
                spaceAfter=8,
            ),

            "body": ParagraphStyle(
                "NexusBody",
                parent=base["BodyText"],
                fontSize=9,
                leading=13,
                spaceAfter=6,
            ),

            "small": ParagraphStyle(
                "NexusSmall",
                parent=base["BodyText"],
                fontSize=7,
                leading=9,
            ),
        }

    # =========================================================
    # DICTIONARY TABLE
    # =========================================================

    @staticmethod
    def _dict_table(
        data: dict[str, Any],
        styles,
        max_rows: int = 40,
    ):

        if not isinstance(data, dict) or not data:

            return Paragraph(
                "No information available.",
                styles["body"],
            )

        rows = [
            [
                Paragraph(
                    "<b>Metric</b>",
                    styles["body"],
                ),
                Paragraph(
                    "<b>Value</b>",
                    styles["body"],
                ),
            ]
        ]

        for index, (
            key,
            value,
        ) in enumerate(data.items()):

            if index >= max_rows:
                break

            rows.append(
                [
                    Paragraph(
                        NexusReportGenerator._text(
                            key
                        ),
                        styles["body"],
                    ),
                    Paragraph(
                        NexusReportGenerator._text(
                            value
                        ),
                        styles["body"],
                    ),
                ]
            )

        table = Table(
            rows,
            colWidths=[
                55 * mm,
                115 * mm,
            ],
            repeatRows=1,
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(
                            "#1f2937"
                        ),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.grey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [
                            colors.white,
                            colors.HexColor(
                                "#f3f4f6"
                            ),
                        ],
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        return table

    # =========================================================
    # DATAFRAME TABLE
    # =========================================================

    @staticmethod
    def _dataframe_table(
        dataframe: pd.DataFrame,
        styles,
        max_rows: int = 15,
        max_columns: int = 8,
    ):

        if not isinstance(
            dataframe,
            pd.DataFrame,
        ):

            return Paragraph(
                "No table available.",
                styles["body"],
            )

        if dataframe.empty:

            return Paragraph(
                "No data available.",
                styles["body"],
            )

        df = dataframe.iloc[
            :max_rows,
            :max_columns,
        ].copy()

        rows = []

        header = []

        for column in df.columns:

            header.append(
                Paragraph(
                    f"<b>{NexusReportGenerator._text(column)}</b>",
                    styles["small"],
                )
            )

        rows.append(header)

        for _, row in df.iterrows():

            rows.append(
                [
                    Paragraph(
                        NexusReportGenerator._text(
                            value
                        ),
                        styles["small"],
                    )
                    for value in row.tolist()
                ]
            )

        column_count = max(
            len(df.columns),
            1,
        )

        width = (
            170 * mm
            / column_count
        )

        table = Table(
            rows,
            colWidths=[
                width
                for _ in df.columns
            ],
            repeatRows=1,
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(
                            "#1f2937"
                        ),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.3,
                        colors.grey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [
                            colors.white,
                            colors.HexColor(
                                "#f9fafb"
                            ),
                        ],
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                ]
            )
        )

        return table

    # =========================================================
    # GENERIC SECTION
    # =========================================================

    @staticmethod
    def _add_result_section(
        story,
        styles,
        results,
        key: str,
        title: str,
    ):

        story.append(
            Paragraph(
                title,
                styles["heading"],
            )
        )

        value = NexusReportGenerator._get(
            results,
            key,
            None,
        )

        if isinstance(
            value,
            pd.DataFrame,
        ):

            story.append(
                NexusReportGenerator._dataframe_table(
                    value,
                    styles,
                )
            )

        elif isinstance(
            value,
            dict,
        ):

            story.append(
                NexusReportGenerator._dict_table(
                    value,
                    styles,
                )
            )

        elif isinstance(
            value,
            (list, tuple),
        ):

            if not value:

                story.append(
                    Paragraph(
                        "No information available.",
                        styles["body"],
                    )
                )

            else:

                for index, item in enumerate(
                    value,
                    start=1,
                ):

                    story.append(
                        Paragraph(
                            f"<b>{index}.</b> "
                            f"{NexusReportGenerator._text(item)}",
                            styles["body"],
                        )
                    )

        else:

            story.append(
                Paragraph(
                    NexusReportGenerator._text(
                        value,
                        "No information available.",
                    ),
                    styles["body"],
                )
            )

    # =========================================================
    # MAIN PDF GENERATOR
    # =========================================================

    @staticmethod
    def generate(
        results: dict[str, Any],
        dataframe: pd.DataFrame | None = None,
        title: str = (
            "NEXUS AI Enterprise "
            "Intelligence Report"
        ),
    ) -> bytes:

        if not isinstance(
            results,
            dict,
        ):

            results = {}

        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title=title,
            author="NEXUS AI",
        )

        styles = (
            NexusReportGenerator
            ._create_styles()
        )

        story = []

        # =====================================================
        # COVER
        # =====================================================

        story.append(
            Spacer(
                1,
                30 * mm,
            )
        )

        story.append(
            Paragraph(
                "NEXUS AI",
                styles["title"],
            )
        )

        story.append(
            Paragraph(
                "Autonomous Enterprise Intelligence",
                styles["subtitle"],
            )
        )

        story.append(
            Paragraph(
                title,
                styles["heading"],
            )
        )

        story.append(
            Spacer(
                1,
                10 * mm,
            )
        )

        metadata = NexusReportGenerator._get(
            results,
            "metadata",
            {},
        )

        if isinstance(
            metadata,
            dict,
        ):

            story.append(
                NexusReportGenerator._dict_table(
                    metadata,
                    styles,
                )
            )

        if isinstance(
            dataframe,
            pd.DataFrame,
        ):

            story.append(
                Spacer(
                    1,
                    8 * mm,
                )
            )

            story.append(
                Paragraph(
                    (
                        f"<b>Rows:</b> "
                        f"{len(dataframe):,}"
                        "&nbsp;&nbsp;&nbsp;"
                        f"<b>Columns:</b> "
                        f"{len(dataframe.columns):,}"
                    ),
                    styles["body"],
                )
            )

        story.append(
            Spacer(
                1,
                25 * mm,
            )
        )

        story.append(
            Paragraph(
                (
                    "Generated: "
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                ),
                styles["subtitle"],
            )
        )

        story.append(PageBreak())

        # =====================================================
        # EXECUTIVE SUMMARY
        # =====================================================

        story.append(
            Paragraph(
                "1. Executive Summary",
                styles["heading"],
            )
        )

        summary = NexusReportGenerator._get(
            results,
            "executive_summary",
            "No executive summary was generated.",
        )

        if isinstance(
            summary,
            dict,
        ):

            story.append(
                NexusReportGenerator._dict_table(
                    summary,
                    styles,
                )
            )

        elif isinstance(
            summary,
            (list, tuple),
        ):

            for index, item in enumerate(
                summary,
                start=1,
            ):

                story.append(
                    Paragraph(
                        f"<b>{index}.</b> "
                        f"{NexusReportGenerator._text(item)}",
                        styles["body"],
                    )
                )

        else:

            story.append(
                Paragraph(
                    NexusReportGenerator._text(
                        summary
                    ),
                    styles["body"],
                )
            )

        # =====================================================
        # CORE ANALYTICS
        # =====================================================

        NexusReportGenerator._add_result_section(
            story,
            styles,
            results,
            "health",
            "2. Intelligence Health",
        )

        NexusReportGenerator._add_result_section(
            story,
            styles,
            results,
            "quality",
            "3. Data Quality",
        )

        NexusReportGenerator._add_result_section(
            story,
            styles,
            results,
            "schema",
            "4. Data Schema",
        )

        NexusReportGenerator._add_result_section(
            story,
            styles,
            results,
            "kpis",
            "5. KPI Intelligence",
        )

        NexusReportGenerator._add_result_section(
            story,
            styles,
            results,
            "correlations",
            "6. Correlation Intelligence",
        )

        NexusReportGenerator._add_result_section(
            story,
            styles,
            results,
            "outliers",
            "7. Outlier Intelligence",
        )

        story.append(PageBreak())

        # =====================================================
        # ADVANCED ANALYTICS
        # =====================================================

        NexusReportGenerator._add_result_section(
            story,
            styles,
            results,
            "drivers",
            "8. Business Drivers",
        )

        NexusReportGenerator._add_result_section(
            story,
            styles,
            results,
            "target_analysis",
            "9. Target Analysis",
        )

        NexusReportGenerator._add_result_section(
            story,
            styles,
            results,
            "distributions",
            "10. Distribution Intelligence",
        )

        NexusReportGenerator._add_result_section(
            story,
            styles,
            results,
            "risks",
            "11. Risk Intelligence",
        )

        NexusReportGenerator._add_result_section(
            story,
            styles,
            results,
            "ml_readiness",
            "12. Machine Learning Readiness",
        )

        # =====================================================
        # RECOMMENDATIONS
        # =====================================================

        NexusReportGenerator._add_result_section(
            story,
            styles,
            results,
            "recommendations",
            "13. Strategic Recommendations",
        )

        # =====================================================
        # DECISION INTELLIGENCE
        # =====================================================

        NexusReportGenerator._add_result_section(
            story,
            styles,
            results,
            "decision_intelligence",
            "14. Decision Intelligence",
        )

        # =====================================================
        # DATA PREVIEW
        # =====================================================

        if (
            isinstance(
                dataframe,
                pd.DataFrame,
            )
            and not dataframe.empty
        ):

            story.append(PageBreak())

            story.append(
                Paragraph(
                    "15. Dataset Preview",
                    styles["heading"],
                )
            )

            story.append(
                NexusReportGenerator._dataframe_table(
                    dataframe.head(15),
                    styles,
                    max_rows=15,
                    max_columns=8,
                )
            )

        # =====================================================
        # FOOTER SUMMARY
        # =====================================================

        story.append(
            Spacer(
                1,
                12 * mm,
            )
        )

        story.append(
            Paragraph(
                (
                    "<b>NEXUS AI</b> generated this report "
                    "from the supplied dataset and analytical "
                    "results."
                ),
                styles["body"],
            )
        )

        # =====================================================
        # BUILD
        # =====================================================

        document.build(
            story,
            onFirstPage=(
                NexusReportGenerator
                ._add_page_number
            ),
            onLaterPages=(
                NexusReportGenerator
                ._add_page_number
            ),
        )

        return buffer.getvalue()


# =============================================================
# PUBLIC CONVENIENCE FUNCTION
# =============================================================

def generate_report(
    results: dict[str, Any],
    dataframe: pd.DataFrame | None = None,
) -> bytes:

    return NexusReportGenerator.generate(
        results=results,
        dataframe=dataframe,
    )