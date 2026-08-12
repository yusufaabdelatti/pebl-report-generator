"""Assessment definitions: CSV parsing, scoring, and reference descriptions.

To add a new PEBL assessment later: add its description, metric list, a
parse_*_csv() function, and a *_scorecard() function following the WCST
pattern below, then wire it into app.py's ASSESSMENT_TYPES.
"""
from datetime import date as date_cls
from datetime import datetime
from typing import Mapping

import pandas as pd

# ---------------------------------------------------------------------------
# Wisconsin Card Sorting Test (WCST) — PEBL "cardsort-pooled.csv" output
# ---------------------------------------------------------------------------

WCST_DESCRIPTION = (
    "The Wisconsin Card Sorting Test (WCST) measures executive function. The "
    "examinee sorts cards by a rule (color, shape, or number) inferred only "
    "from feedback; the rule changes without warning. It reflects cognitive "
    "flexibility, abstract reasoning, and strategy-shifting ability — often "
    "impaired in frontal-lobe and other neurological or psychiatric conditions."
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
    "Perseverative Errors — Typical <10% · Mildly elevated 10–20% · Notably "
    "elevated >20%. Conceptual-Level Responses — Typical ≥70% · Mildly "
    "reduced 50–70% · Notably reduced <50%. General reference ranges, not "
    "formal age/education-corrected norms."
)


def parse_wcst_csv(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    df.columns = [c.strip() for c in df.columns]
    return df


def wcst_row_label(row: Mapping) -> str:
    sub = row.get("subNum", "unknown")
    ts = row.get("TimeStamp", "")
    return f"{sub} — {ts}"


def parse_wcst_timestamp(ts) -> date_cls | None:
    """Parse PEBL's TimeStamp column (e.g. 'Thu Aug 13 00:12:20 2026') into a date."""
    if not ts:
        return None
    try:
        return datetime.strptime(str(ts).strip(), "%a %b %d %H:%M:%S %Y").date()
    except ValueError:
        return None


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
    "Performance IQ (Non-Verbal) reflects fluid, non-verbal reasoning — "
    "pattern recognition, spatial reasoning, and visual problem-solving — "
    "largely independent of language ability. It's derived from measures such "
    "as Wechsler-family performance indices or Raven's Progressive Matrices."
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

PIQ_REFERENCE_NOTE = (
    "Very Superior 130+ · Superior 120–129 · High Average 110–119 · Average "
    "90–109 · Low Average 80–89 · Borderline 70–79 · Extremely Low <70 "
    "(Wechsler-scale classification)."
)


def classify_iq(score: float) -> str:
    for lo, hi, label in PIQ_BANDS:
        if lo <= score < hi:
            return label
    return "Unclassified"


# ---------------------------------------------------------------------------
# Memory Assessment (Number-Finding & Visual Scan) — manually entered, no CSV
# ---------------------------------------------------------------------------

MEMORY_DESCRIPTION = (
    "This assessment evaluates memory and visual scanning ability, reflecting "
    "visual scanning speed, sustained attention, processing speed, and "
    "spatial working memory."
)

# (lower bound minutes inclusive, upper bound minutes exclusive, label)
MEMORY_TIME_BANDS = [
    (0, 16, "Excellent"),
    (16, 19, "Good"),
    (19, 22, "Passed"),
    (22, float("inf"), "Failed"),
]

MEMORY_REFERENCE_NOTE = (
    "Excellent ≤15 min · Good 16–18 min · Passed 19–21 min · Failed ≥22 min "
    "(per source tool's scoring guide)."
)


def classify_memory_time(total_minutes: float) -> str:
    for lo, hi, label in MEMORY_TIME_BANDS:
        if lo <= total_minutes < hi:
            return label
    return "Failed"


def memory_scorecard(minutes: int, seconds: int, errors: int) -> list[dict]:
    total_minutes = minutes + seconds / 60
    band = classify_memory_time(total_minutes)
    return [
        {
            "label": "Completion Time",
            "value": f"{minutes:02d}:{seconds:02d}",
            "classification": band,
        },
        {
            "label": "Errors",
            "value": errors,
            "classification": "",
        },
    ]
