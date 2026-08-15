# AI Response Quality Evaluator — Frontend Redesign

A complete, modern Streamlit dashboard for the multi-agent evaluation system.
**No backend logic or API contracts were changed.** This is frontend-only:
layout, visualization, and presentation.

## Run it

```bash
cd frontend
pip install -r requirements.txt
export EVAL_BACKEND_URL="http://localhost:8000"   # optional, defaults to this
streamlit run app.py
```

If the FastAPI backend isn't running, the app automatically falls back to
realistic demo data (with a visible "Backend Offline (Demo Mode)" badge) so
you can still present or screenshot every page. Nothing about this fallback
touches backend logic — it only fires when a real request fails.

## Folder structure

```
frontend/
├── app.py                     # entrypoint: page config, sidebar nav, routing
├── requirements.txt
├── theme/
│   └── style.css               # dark, modern dashboard theme (all custom CSS lives here)
├── utils/
│   └── api_client.py           # calls existing FastAPI endpoints; demo-mode fallback only
├── components/                 # reusable, presentation-only building blocks
│   ├── badges.py                # badge / pill / card / metric-tile helpers
│   ├── score_ring.py             # circular (donut) score indicator, Plotly
│   ├── pipeline_viz.py           # horizontal agent pipeline with done/active states
│   ├── charts.py                 # radar chart, score comparison bar, distribution histogram
│   └── result_cards.py           # one card component per agent (relevance/accuracy/…)
└── pages_content/
    ├── home.py                   # landing / product-style dashboard
    ├── about.py                  # architecture, agents, tech stack, future scope
    ├── single_evaluation.py      # input form → animated pipeline → full results + report
    └── benchmark_validation.py   # CSV upload → batch run → tables + charts + CSV export
```

## What maps to each requirement

| Requirement | Where |
|---|---|
| Modern / dark / OpenAI-style UI | `theme/style.css`, injected once in `app.py` |
| Multi-agent architecture diagram | `pages_content/home.py`, `about.py` (ASCII diagram + pipeline component) |
| Circular score indicators | `components/score_ring.py` |
| Progress bars / badges / expandable reasoning | `components/result_cards.py` |
| Pipeline visualization with live states | `components/pipeline_viz.py`, animated in `single_evaluation.py` |
| Radar chart / score comparison / distribution | `components/charts.py` |
| Benchmark dashboard (CSV, batch run, download) | `pages_content/benchmark_validation.py` |
| Milestone / team / features on Home | `pages_content/home.py` |

## Wiring to your real backend

`utils/api_client.py` calls these endpoints exactly as documented and returns
the JSON untouched:

- `POST /evaluate/relevance`
- `POST /evaluate/accuracy`
- `POST /evaluate/hallucination`
- `POST /evaluate/completeness`
- `POST /evaluate/verdict`
- `POST /evaluate/all` *(used by both Single Evaluation and Benchmark Validation)*

If your Pydantic request schema field names differ slightly from
`{"question": ..., "response": ..., "reference_answer": ...}`, update the
`payload` dict inside `evaluate_dimension()` / `evaluate_all()` in
`utils/api_client.py` — that's the only place request shape is built.

## Notes for the presentation

- The sidebar shows a live **Backend Connected / Offline** badge (pings `/`),
  useful for demoing confidently even on flaky wifi.
- The Single Evaluation page runs a short animated pipeline (stage-by-stage
  "done → active" states) before showing results — reads well live.
- Every score component only expects the fields already defined in your
  documented API responses (score, semantic_similarity, topic_match,
  factually_correct, evidence, supported_claims, hallucinated_claims,
  coverage_percentage, total_aspects, extracted_aspects, covered_aspects,
  missing_aspects, overall_score, final_verdict, quality_gate_passed,
  weighted_score_breakdown, strengths, weaknesses, consolidated_reasoning).

## Optional next steps

- Add `streamlit-lottie` or `streamlit-elements` if you want richer
  animation on the pipeline stage transitions.
- Add a PDF export of the Final Report using the existing `pdf` skill
  workflow if you want a downloadable report artifact per evaluation.
- If you want true multi-page URLs (`/Home`, `/About`, etc.) instead of a
  sidebar radio, move each `pages_content/*.py render()` body into a
  `pages/1_🏠_Home.py`-style file — the components/ and utils/ layers need
  no changes either way.
