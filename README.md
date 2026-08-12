# PEBL Assessment Report Generator

Turn PEBL (Psychology Experiment Building Language) CSV output into a clean,
signed PDF report with AI-assisted interpretation — no manual template
filling.

Currently supported assessments:

- **Wisconsin Card Sorting Test (WCST)** — upload PEBL's `cardsort-pooled.csv`
  output.
- **Performance IQ (Non-Verbal)** — manually enter a single IQ score (no CSV;
  for scores obtained outside PEBL).

You can add several assessments to the same report — each gets its own
section, and if there's more than one, an integrative "Overall Summary" is
added at the end. More PEBL assessments can be added later in
[assessments.py](assessments.py).

## How it works

1. Fill in the report date and your name (signature) in the sidebar.
2. Pick an assessment, upload its CSV (or enter the score), and add it to the
   report. Repeat for as many assessments as you want in this report.
3. Click **Generate PDF Report** — GROQ's LLM writes the interpretive
   narrative for each section from the actual scores (it's told not to
   invent norms or diagnoses).
4. Download the PDF.

## Local setup

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edit .streamlit/secrets.toml and paste your free GROQ API key
streamlit run app.py
```

Get a free GROQ API key at [console.groq.com](https://console.groq.com/keys).

## Deploying on Streamlit Community Cloud

1. Push this folder to its own GitHub repo (see below).
2. Go to [share.streamlit.io](https://share.streamlit.io), create a new app
   pointing at that repo and `app.py`.
3. In the app's **Settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "your-groq-api-key-here"
   ```
4. Deploy. `.streamlit/secrets.toml` is gitignored so your real key never
   gets committed.

## Adding another PEBL assessment later

1. In [assessments.py](assessments.py), add a description string, a metrics
   list (or manual-entry fields), a `parse_*_csv()` function if it's
   CSV-based, and a `*_scorecard()` function that returns
   `[{"label", "value", "classification"}, ...]`.
2. Add the new option to `ASSESSMENT_TYPES` in [app.py](app.py) and wire up
   its input UI + the branch that builds its `sections` entry when
   generating the report.
