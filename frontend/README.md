# AI Response Quality Evaluator Agent — Frontend

Streamlit dashboard for the multi-agent AI response evaluation system.
Four pages: Single Evaluation, Benchmark Validation (batch), Dashboard,
and About — all talking to the FastAPI backend, with graceful fallback to
demo data if the backend is unreachable.

## Structure

```
frontend/
├── app.py                          Nav, theme, page routing
├── pages_content/
│   ├── home.py / about.py          Static content
│   ├── single_evaluation.py        One question/response through the full pipeline; PDF export
│   ├── benchmark_validation.py     CSV batch upload -> run -> analytics -> CSV/Excel/JSON/PDF export
│   └── dashboard.py                Cross-history analytics: trends, hallucination frequency, system comparison
├── components/
│   ├── badges.py                   card(), section_label(), metric_tile(), badge_html()
│   ├── result_cards.py             Per-dimension result cards (Relevance/Accuracy/Hallucination/Completeness/Verdict)
│   ├── charts.py / batch_charts.py / batch_summary.py   Radar, bar, distribution, pass/fail pie, trend line
│   ├── score_ring.py / pipeline_viz.py
├── utils/
│   ├── api_client.py                All backend HTTP calls, incl. response normalization + history fetchers
│   ├── csv_parser.py                Batch CSV validation (missing columns, missing values, encoding fallback)
│   ├── batch_processor.py           Sequential /evaluate/all runner with per-row error isolation
│   ├── download_utils.py            CSV/Excel/JSON export
│   └── pdf_export.py                Structured PDF reports (Single + Batch)
├── tests/                           E2E tests driving the real pages via Streamlit's AppTest
├── conftest.py                      Puts frontend/ on sys.path for pytest
└── theme/style.css
```

## Running

```bash
pip install -r requirements.txt
export EVAL_BACKEND_URL="http://localhost:8000"   # optional, defaults to this
streamlit run app.py
```

If the FastAPI backend isn't running, the app falls back to demo data
(with a visible "Backend Offline (Demo Mode)" badge in the sidebar) so
every page still renders — nothing about this fallback touches real
scoring logic; it only fires when a real request actually fails.

## Running tests

```bash
pytest tests/ -v
```

21 end-to-end tests driving the **real** pages through Streamlit's
[`AppTest`](https://docs.streamlit.io/library/api-reference/app-testing) —
filling in actual widgets, clicking actual buttons, reading back actual
rendered output. No live backend needed: each test mocks the network
boundary and lets everything above it (page logic, component rendering,
chart construction, PDF generation) run for real.

**A mocking-layer note that mattered in practice:** `batch_processor.py`
and `dashboard.py` both do `from utils.api_client import X` (direct name
imports), not `import utils.api_client as api_client`. That means a mock
has to target `batch_processor.evaluate_all` / `dashboard.get_history_summary`
etc. directly — patching `api_client.evaluate_all` has no effect on an
already-bound name in another module's namespace. Getting this wrong
previously let a real bug (`_normalize_all()` silently dropping the `rag`
key) pass an earlier round of manual testing undetected, because the test
mocked one layer too high and never actually exercised the buggy
normalization function. The test files here mock at the correct layer for
each page.

| File | Covers |
|---|---|
| `test_single_evaluation_e2e.py` | Full pipeline flow, empty-input handling, PDF export, the "Unverified" badge fix, the negative-similarity crash fix, backend-unreachable fallback |
| `test_benchmark_validation_e2e.py` | Sample-dataset flow, all 4 export buttons, tag propagation to every row, malformed-input handling |
| `test_dashboard_e2e.py` | Empty-history state, populated multi-section rendering, single-system vs. two-system comparison views |

## Key features by page

**Single Evaluation** — one question/response through all five agents.
Optional reference answer (falls back to RAG retrieval, or an honest
"Unverified" state if nothing relevant exists). Optional System/Model Name
tag. PDF report export.

**Benchmark Validation** — CSV upload (`question`, `response`,
`reference_answer` columns) or a built-in sample dataset. Validates before
running (missing columns, missing values reported not silently dropped).
Sequential evaluation with live progress/ETA, per-row error isolation
(one bad row doesn't kill the batch). Optional System Name + Run Label
tags. Analytics: distribution, pass/fail pie, radar/bar per dimension,
score trend, standout responses (best/worst/highest-accuracy/lowest-
hallucination-risk). CSV/Excel/JSON/PDF export.

**Dashboard** — aggregates *every* evaluation ever run, single or batch,
persisted server-side in SQLite (not session state — survives a restart).
Overall summary, average dimension scores, hallucination frequency,
quality-gate pass/fail, quality trends across batch runs over time, and
side-by-side comparison of two or more tagged AI systems — see
`TWO_SYSTEM_DEMO.md` at the project root for a walkthrough.
