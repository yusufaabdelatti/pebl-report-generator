"""Builds the final PDF report using reportlab."""
import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ACCENT = colors.HexColor("#2E5EAA")
LIGHT_BG = colors.HexColor("#F2F5FA")
GRID = colors.HexColor("#CCCCCC")
META_GRAY = colors.HexColor("#555555")


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "ReportTitle", parent=styles["Title"], textColor=ACCENT, fontSize=20, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "SectionHeading", parent=styles["Heading2"], textColor=ACCENT, spaceBefore=16, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "Meta", parent=styles["Normal"], textColor=META_GRAY, fontSize=9,
    ))
    styles.add(ParagraphStyle(
        "Body", parent=styles["Normal"], fontSize=10.5, leading=15,
    ))
    return styles


def build_pdf(
    patient_id: str,
    report_date: date,
    clinician_name: str,
    sections: list[dict],
    overall_summary: str | None,
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=LETTER,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        title="Cognitive Assessment Report",
    )
    styles = _styles()
    story = []

    story.append(Paragraph("Cognitive Assessment Report", styles["ReportTitle"]))
    story.append(Paragraph(
        f"Subject/Patient ID: <b>{patient_id or '—'}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"Report Date: <b>{report_date.strftime('%B %d, %Y')}</b>",
        styles["Meta"],
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceBefore=8, spaceAfter=12))

    for i, section in enumerate(sections):
        if i > 0:
            story.append(PageBreak())
        story.append(Paragraph(section["name"], styles["SectionHeading"]))
        if section.get("date"):
            story.append(Paragraph(f"Assessment Date: <b>{section['date'].strftime('%B %d, %Y')}</b>", styles["Meta"]))
            story.append(Spacer(1, 4))
        story.append(Paragraph(section["description"], styles["Body"]))
        story.append(Spacer(1, 8))

        table_data = [["Measure", "Score", "Reference"]]
        for row in section["scorecard"]:
            table_data.append([row["label"], str(row["value"]), row.get("classification", "")])
        table = Table(table_data, colWidths=[2.6 * inch, 1.2 * inch, 2.0 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ("GRID", (0, 0), (-1, -1), 0.5, GRID),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(table)
        story.append(Spacer(1, 10))

        story.append(Paragraph("<b>Interpretation</b>", styles["Body"]))
        story.append(Paragraph(section["narrative"], styles["Body"]))

        if section.get("reference_note"):
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"<i>{section['reference_note']}</i>", styles["Meta"]))

    if overall_summary:
        story.append(Paragraph("Overall Summary", styles["SectionHeading"]))
        story.append(Paragraph(overall_summary, styles["Body"]))

    story.append(Spacer(1, 36))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#999999")))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Signed: <b>{clinician_name or '_' * 30}</b>", styles["Body"]))
    story.append(Paragraph(report_date.strftime("%B %d, %Y"), styles["Meta"]))

    doc.build(story)
    return buf.getvalue()
