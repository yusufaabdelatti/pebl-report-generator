"""Thin wrapper around the GROQ chat completion API for report narrative generation."""
import streamlit as st
from groq import Groq

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = (
    "You are a clinical psychology assistant drafting the interpretive "
    "narrative for a cognitive assessment report section. Write in clear, "
    "professional clinical-report language. Base your interpretation strictly "
    "on the scores and reference notes provided — never invent norms, "
    "percentiles, or diagnoses. Do not provide a diagnosis. Keep it to one "
    "tight paragraph (roughly 60-90 words) written in the third person about "
    "'the examinee'. Do not restate the raw numbers as a list — synthesize "
    "them into a brief narrative about the pattern of performance."
)


def _client() -> Groq:
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to .streamlit/secrets.toml locally, "
            "or under your Streamlit Cloud app's Settings -> Secrets."
        )
    return Groq(api_key=api_key)


def generate_section_narrative(
    assessment_name: str,
    description: str,
    score_lines: list[str],
    reference_note: str = "",
) -> str:
    client = _client()
    scores_block = "\n".join(f"- {line}" for line in score_lines)
    user_prompt = (
        f"Assessment: {assessment_name}\n\n"
        f"What this assessment measures: {description}\n\n"
        f"Scores obtained:\n{scores_block}\n\n"
        + (f"Interpretive reference notes: {reference_note}\n\n" if reference_note else "")
        + "Write the interpretive narrative paragraph for this section of the report."
    )
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=250,
    )
    return resp.choices[0].message.content.strip()


def generate_overall_summary(sections: list[dict]) -> str:
    client = _client()
    joined = "\n\n".join(f"{s['name']}: {s['narrative']}" for s in sections)
    user_prompt = (
        "Below are the interpretive narratives already written for each "
        "assessment in this multi-assessment report:\n\n"
        f"{joined}\n\n"
        "Write one brief integrative summary paragraph (roughly 50-70 words) "
        "that ties the findings across these assessments together for the "
        "reader, noting any converging or contrasting patterns. Do not "
        "introduce new scores or diagnoses."
    )
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=180,
    )
    return resp.choices[0].message.content.strip()
