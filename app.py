"""Streamlit app: build a multi-assessment cognitive report from PEBL CSV
output (plus manually-entered scores), with GROQ-generated interpretation."""
from datetime import date

import streamlit as st

from assessments import (
    PIQ_DESCRIPTION,
    WCST_DESCRIPTION,
    WCST_REFERENCE_NOTE,
    classify_iq,
    parse_wcst_csv,
    wcst_row_label,
    wcst_scorecard,
)
from groq_client import generate_overall_summary, generate_section_narrative
from pdf_report import build_pdf

st.set_page_config(page_title="PEBL Assessment Report Generator", page_icon="🧠", layout="centered")

if "assessments" not in st.session_state:
    st.session_state.assessments = []
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None

st.title("🧠 PEBL Assessment Report Generator")
st.caption("Add one or more assessments, then generate a single AI-assisted PDF report.")

with st.sidebar:
    st.header("Report Details")
    patient_id = st.text_input("Patient / Subject ID (optional — auto-filled from CSV if left blank)")
    report_date = st.date_input("Report Date", value=date.today())
    clinician_name = st.text_input("Clinician Name (signature)")

st.divider()
st.subheader("1. Add an assessment")

ASSESSMENT_TYPES = ["Wisconsin Card Sorting Test (WCST)", "Performance IQ (Non-Verbal)"]
assessment_type = st.selectbox("Assessment", ASSESSMENT_TYPES)

if assessment_type == "Wisconsin Card Sorting Test (WCST)":
    uploaded = st.file_uploader(
        "Upload PEBL cardsort-pooled.csv",
        type="csv",
        key=f"wcst_upload_{len(st.session_state.assessments)}",
    )
    if uploaded is not None:
        df = parse_wcst_csv(uploaded)
        if len(df) > 1:
            options = {wcst_row_label(row): i for i, row in df.iterrows()}
            choice = st.selectbox("Multiple runs found — choose the one for this report", list(options.keys()))
            row = df.iloc[options[choice]].to_dict()
        else:
            row = df.iloc[0].to_dict()
        st.dataframe(df.iloc[[0]] if len(df) == 1 else df, use_container_width=True)
        if st.button("Add WCST to report"):
            st.session_state.assessments.append({
                "type": "wcst",
                "name": "Wisconsin Card Sorting Test (WCST)",
                "row": row,
            })
            st.rerun()

elif assessment_type == "Performance IQ (Non-Verbal)":
    piq_score = st.number_input("Performance IQ Score", min_value=40, max_value=180, value=100, step=1)
    if st.button("Add Performance IQ to report"):
        st.session_state.assessments.append({
            "type": "piq",
            "name": "Performance IQ (Non-Verbal)",
            "score": piq_score,
        })
        st.rerun()

st.divider()
st.subheader(f"2. Assessments in this report ({len(st.session_state.assessments)})")

if not st.session_state.assessments:
    st.info("No assessments added yet.")
else:
    for i, a in enumerate(st.session_state.assessments):
        cols = st.columns([5, 1])
        with cols[0]:
            if a["type"] == "wcst":
                st.write(f"**{i + 1}. {a['name']}** — subject `{a['row'].get('subNum', '?')}`")
            else:
                st.write(f"**{i + 1}. {a['name']}** — score {a['score']}")
        with cols[1]:
            if st.button("Remove", key=f"remove_{i}"):
                st.session_state.assessments.pop(i)
                st.session_state.pdf_bytes = None
                st.rerun()

st.divider()
st.subheader("3. Generate report")

if st.button("Generate PDF Report", type="primary", disabled=not st.session_state.assessments):
    with st.spinner("Generating interpretive narrative with GROQ..."):
        try:
            sections = []
            derived_patient_id = patient_id

            for a in st.session_state.assessments:
                if a["type"] == "wcst":
                    row = a["row"]
                    if not derived_patient_id:
                        derived_patient_id = str(row.get("subNum", ""))
                    cards = wcst_scorecard(row)
                    score_lines = [
                        f"{c['label']}: {c['value']}" + (f" ({c['classification']})" if c["classification"] else "")
                        for c in cards
                    ]
                    narrative = generate_section_narrative(
                        a["name"], WCST_DESCRIPTION, score_lines, WCST_REFERENCE_NOTE
                    )
                    sections.append({
                        "name": a["name"],
                        "description": WCST_DESCRIPTION,
                        "scorecard": cards,
                        "narrative": narrative,
                        "reference_note": WCST_REFERENCE_NOTE,
                    })

                elif a["type"] == "piq":
                    band = classify_iq(a["score"])
                    cards = [{"label": "Performance IQ (Non-Verbal)", "value": a["score"], "classification": band}]
                    score_lines = [f"Performance IQ: {a['score']} ({band})"]
                    narrative = generate_section_narrative(a["name"], PIQ_DESCRIPTION, score_lines)
                    sections.append({
                        "name": a["name"],
                        "description": PIQ_DESCRIPTION,
                        "scorecard": cards,
                        "narrative": narrative,
                        "reference_note": "",
                    })

            overall_summary = generate_overall_summary(sections) if len(sections) > 1 else None

            st.session_state.pdf_bytes = build_pdf(
                derived_patient_id, report_date, clinician_name, sections, overall_summary
            )
            st.success("Report generated.")
        except Exception as e:
            st.error(str(e))

if st.session_state.pdf_bytes:
    st.download_button(
        "Download PDF Report",
        data=st.session_state.pdf_bytes,
        file_name=f"assessment_report_{report_date.isoformat()}.pdf",
        mime="application/pdf",
    )
