"""Assessment definitions: CSV parsing, scoring, and reference descriptions.

To add a new PEBL assessment later: add its description, metric list, a
parse_*_csv() function, and a *_scorecard() function following the WCST
pattern below, then wire it into app.py's ASSESSMENT_TYPES.
"""
from typing import Mapping

import pandas as pd

# ---------------------------------------------------------------------------
# Wisconsin Card Sorting Test (WCST) — PEBL "cardsort-pooled.csv" output
# ---------------------------------------------------------------------------

WCST_DESCRIPTION = (
    "The Wisconsin Card Sorting Test (WCST), implemented here via PEBL's Berg "
    "Card Sorting Task, is a widely used neuropsychological measure of executive "
    "function. It requires the examinee to sort cards according to a rule "
    "(color, shape, or number) inferred only from trial-and-error feedback; the "
    "rule changes periodically without warning. Performance indexes cognitive "
    "flexibility, abstract reasoning, working memory, and the ability to shift "
    "strategies in response to changing feedback — abilities that are commonly "
    "impaired in frontal-lobe dysfunction and a range of neurological and "
    "psychiatric conditions."
)

# (csv_column, display label, definition, higher_is_better)
WCST_METRICS = [
    ("numcats", "Categories Completed",
     "Number of full sorting categories the examinee completed.", True),
    ("numTrials", "Trials Administered",
     "Total number of card-sort trials completed in this run.", None),
    ("totCorr", "Total Correct Responses",
     "Number of trials sorted correctly.", True),
    ("err", "Total Errors",
     "Number of trials sorted incorrectly (Trials − Correct).", False),
    ("totPers", "Perseverative Responses",
     "Responses that kept applying a rule that had just stopped working.", False),
    ("totPersErr", "Perseverative Errors",
     "Incorrect responses that repeated the previously correct (now outdated) "
     "rule — the classic marker of reduced cognitive flexibility.", False),
    ("nonp", "Non-Perseverative Errors",
     "Errors that were not tied to the old, outdated rule.", False),
    ("totUnique", "Unique Errors",
     "Errors that did not match any of the sorting rules being tracked.", False),
    ("firstcat", "Trials to Complete First Category",
     "How many trials it took to work out the very first sorting rule.", False),
    ("failuretomaintain", "Failure to Maintain Set",
     "Number of times the examinee lost track of a rule right after showing "
     "they had learned it (5+ correct in a row, then an error, before the "
     "category was finished).", False),
    ("learningtolearn", "Learning-to-Learn Index",
     "Change in sorting efficiency across successive categories — reflects "
     "whether the examinee got more efficient at detecting new rules as the "
     "test went on. Interpret direction cautiously.", None),
    ("conceptual", "Conceptual-Level Responses",
     "Count of consecutive correct responses occurring in runs of 3 or more, "
     "reflecting rule-based (rather than trial-and-error) sorting.", True),
    ("totPersPAR", "Perseverative Responses (PAR method)",
     "Perseverative response count computed using the Perseverative-Ambiguous "
     "-Response (PAR) scoring method.", False),
    ("totPersErrPar", "Perseverative Errors (PAR method)",
     "Perseverative error count computed using the PAR scoring method.", False),
]

WCST_REFERENCE_NOTE = (
    "Reference bands below are general, literature-based rules of thumb (e.g., "
    "% perseverative errors under ~10% is typically considered within a "
    "typical range, 10–20% mildly elevated, and above ~20% notably elevated). "
    "They are NOT a substitute for formal age- and education-corrected "
    "normative comparisons (e.g., Heaton et al. standardization tables), which "
    "require demographic data this app does not collect. Treat all bands as "
    "descriptive context only, not a standardized score."
)


def parse_wcst_csv(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    df.columns = [c.strip() for c in df.columns]
    return df


def wcst_row_label(row: Mapping) -> str:
    sub = row.get("subNum", "unknown")
    ts = row.get("TimeStamp", "")
    return f"{sub} — {ts}"


def _fmt_value(v):
    """Clean up floats so tiny floating-point noise (e.g. 1.08e-19) reads as 0."""
    if isinstance(v, float):
        if abs(v) < 1e-6:
            return 0
        if v == int(v):
            return int(v)
        return round(v, 3)
    return v


def wcst_scorecard(row: Mapping) -> list[dict]:
    cards = []
    for col, label, definition, higher_is_better in WCST_METRICS:
        if col not in row:
            continue
        cards.append({
            "label": label,
            "value": _fmt_value(row[col]),
            "definition": definition,
            "higher_is_better": higher_is_better,
            "classification": "",
        })

    num_trials = float(row["numTrials"]) if row.get("numTrials") else None

    if num_trials and "conceptual" in row:
        pct = round(float(row["conceptual"]) / num_trials * 100, 1)
        cards.append({
            "label": "% Conceptual-Level Responses",
            "value": f"{pct}%",
            "definition": "Conceptual-level responses expressed as a percentage of all trials administered.",
            "higher_is_better": True,
            "classification": classify_pct_conceptual(pct),
        })

    if num_trials and "totPersErr" in row:
        pct = round(float(row["totPersErr"]) / num_trials * 100, 1)
        cards.append({
            "label": "% Perseverative Errors",
            "value": f"{pct}%",
            "definition": "Perseverative errors expressed as a percentage of all trials administered.",
            "higher_is_better": False,
            "classification": classify_pct_perseverative_errors(pct),
        })

    return cards


def classify_pct_perseverative_errors(pct: float) -> str:
    if pct < 10:
        return "Within typical range"
    if pct < 20:
        return "Mildly elevated"
    return "Notably elevated"


def classify_pct_conceptual(pct: float) -> str:
    if pct >= 70:
        return "Within typical range"
    if pct >= 50:
        return "Mildly reduced"
    return "Notably reduced"


# ---------------------------------------------------------------------------
# Performance IQ (Non-Verbal) — manually entered score, no CSV
# ---------------------------------------------------------------------------

PIQ_DESCRIPTION = (
    "Performance IQ (Non-Verbal) summarizes performance on a non-verbal "
    "reasoning measure (e.g., a performance/perceptual-reasoning IQ index such "
    "as those derived from Wechsler-family scales, Raven's Progressive "
    "Matrices, or comparable instruments). It reflects fluid, non-verbal "
    "problem-solving — pattern recognition, spatial reasoning, and visual "
    "analysis — largely independent of language ability or acquired verbal "
    "knowledge. This score is entered directly rather than derived from a "
    "PEBL CSV file."
)

# Standard Wechsler-scale IQ classification bands (mean 100, SD 15).
PIQ_BANDS = [
    (130, float("inf"), "Very Superior"),
    (120, 130, "Superior"),
    (110, 120, "High Average"),
    (90, 110, "Average"),
    (80, 90, "Low Average"),
    (70, 80, "Borderline"),
    (float("-inf"), 70, "Extremely Low"),
]


def classify_iq(score: float) -> str:
    for lo, hi, label in PIQ_BANDS:
        if lo <= score < hi:
            return label
    return "Unclassified"
