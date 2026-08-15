# AI Response Quality Evaluator Agent — Project Report

## 1. Overview

A multi-agent system that evaluates AI-generated responses across four
independent quality dimensions — Relevance, Accuracy, Hallucination, and
Completeness — combined by a Verdict Agent into a weighted overall score
and a PASS/FAIL quality gate. Supports single-response evaluation,
CSV-driven batch evaluation, RAG-grounded scoring against a TruthfulQA/
SQuAD knowledge base, persistent cross-session history, an analytics
dashboard, and PDF report export.

**Stack:** FastAPI + Pydantic + SQLite (backend), Streamlit + Plotly
(frontend), Sentence-Transformers (`all-MiniLM-L6-v2`) + ChromaDB (RAG),
reportlab (PDF).

## 2. Architecture

```
Question + Response (+ optional Reference Answer)
        │
        ▼
EvaluationOrchestrator ──► RAG fallback (if no reference supplied):
        │                    retrieve closest KB passage, reject if not
        │                    close enough (cosine distance > 0.75)
        ▼
┌──────────────────────────────────────────────────┐
│ Relevance │ Accuracy │ Hallucination │ Completeness │  (independent agents)
└──────────────────────────────────────────────────┘
        │
        ▼
   Verdict Agent (weighted sum + independent quality gate)
        │
        ▼
   History Store (SQLite) ──► Dashboard, PDF export
```

Full architectural review — strengths, weaknesses, and every issue found
before remediation — is preserved in `backend-architecture-review.md`
from earlier in the project; this report summarizes what was actually
fixed against that review, milestone by milestone.

## 3. Milestone-by-Milestone Summary

### Milestone 1 — Research, Input Module, Reference Knowledge Base
- `EvaluationRequest` schema with real field validation (empty/whitespace
  question or response rejected with a 422, not silently scored).
- Knowledge base built from TruthfulQA + SQuAD (chunking, embedding,
  ChromaDB indexing) — **and, unlike the initial implementation, actually
  wired into live evaluation**, not just built and left disconnected. This
  was the single biggest gap found in the architecture review and was
  closed by the `EvaluationOrchestrator`'s RAG fallback.

### Milestone 2 — Relevance, Accuracy, Hallucination Agents
- All three agents implemented and unit-tested (bucketed cosine-similarity
  scoring for Relevance/Accuracy; claim-level best-match verification for
  Hallucination).
- **Honest handling of missing evidence.** Originally, when no reference
  answer was available, Accuracy and Hallucination both defaulted to
  confidently negative language ("factually incorrect", "contains
  significant hallucinations") even though nothing had actually been
  checked — a true statement like "New Delhi is the capital of India"
  could be reported as a hallucinated claim purely because there was
  nothing to verify it against. Fixed with an explicit `verifiable` flag
  threaded from the agents through to the Verdict Agent's own
  weaknesses/failed-conditions text, so the *entire* report — per-dimension
  reasoning, verdict summary, and PDF — consistently says "could not be
  verified" instead of asserting a false negative. The numeric score and
  PASS/FAIL outcome are unchanged (still conservative); only the wording
  is now accurate. Regression-tested in both the unit suite and the E2E suite.

### Milestone 3 — Completeness, Verdict, Batch Evaluation
- Completeness Agent (keyword/pattern-based aspect coverage) and Verdict
  Agent (fixed weights: Relevance 0.25, Accuracy 0.35, Hallucination 0.25,
  Completeness 0.15; independent quality gate failing on any of
  Relevance/Accuracy/Hallucination `< 4` regardless of the weighted average).
- Batch Evaluation: CSV upload → validation (missing columns, missing
  values reported not silently dropped, encoding fallback) → sequential
  evaluation with per-row error isolation and live progress/ETA →
  analytics (distribution, pass/fail, radar/bar, standout responses) →
  CSV/Excel/JSON export. Reuses the existing `/evaluate/all` endpoint
  with zero backend changes required — validating that endpoint's
  original design was generic enough for both single and batch use.

### Milestone 4 — Dashboard, PDF Export, Testing, Documentation
- **Dashboard.** Backed by a new SQLite persistence layer
  (`history_store.py`) that every evaluation is automatically recorded to
  — the one genuine prerequisite this milestone needed, since batch
  results previously lived only in Streamlit session state and vanished
  on refresh. Shows overall summary, average dimension scores,
  hallucination frequency, pass/fail rate, quality trends across batch
  runs over time, and side-by-side comparison of two or more AI systems
  tagged via an optional System Name field on both Single and Batch
  evaluation.
- **PDF Export.** Structured reports (reportlab) for both Single and
  Batch evaluation: per-dimension breakdown with reasoning, flagged/failed
  responses, and data-driven improvement recommendations (genuinely
  derived from which dimension scored lowest in that specific batch, not
  a canned template — verified by testing against batches where different
  dimensions were deliberately the weakest).
- **End-to-end testing.** 73 automated tests total:
  - 37 backend unit tests (agent logic, verdict math, benchmark validation)
  - 15 backend integration tests (`test_e2e_integration.py`) — the real
    FastAPI app via `TestClient`: HTTP validation, the full evaluation
    contract, RAG fallback firing/not firing, tagged persistence,
    history aggregation, clean error handling
  - 21 frontend end-to-end tests (`frontend/tests/`) — the real Streamlit
    pages via `AppTest`: full user flows for Single Evaluation, Batch
    Evaluation, and Dashboard, plus regression tests locking in every bug
    found and fixed during manual testing (the negative-similarity crash,
    the dropped-RAG-key normalization bug, the unverified-dimension
    mislabeling)
- **Documentation.** This report, updated backend/frontend READMEs, and
  `TWO_SYSTEM_DEMO.md` — a concrete walkthrough for demonstrating the
  platform against two genuinely different AI systems' outputs (not the
  same data relabeled, which was a mistake caught and corrected during
  the project's own testing).

## 4. Notable Bugs Found and Fixed During Development

Listed because *how* they were found matters as much as the fixes — every
one below was caught by actually running the code (unit test, integration
test, or manual reproduction with real data), not by inspection alone:

| Bug | Found by | Fix |
|---|---|---|
| RAG knowledge base built but never called by live evaluation | Full-repo grep during architecture review | Wired into `EvaluationOrchestrator` with a relevance-gated fallback |
| Field-name mismatch (`hallucination_score`/`completeness_score` vs. generic `score`) silently zeroing UI score rings | Tracing the actual response shape against frontend expectations | Backward-compatible key aliasing in `api_client.py` |
| `_normalize_all()` silently dropping the `rag` response key | A real user report of missing UI messaging; root-caused by mocking at the correct layer instead of the layer an earlier test had used | Explicit key preservation, with a dedicated regression test |
| `st.progress()` crash on negative cosine similarity | Real user-submitted traceback | Clamp both bounds, not just the upper one; regression test with the exact reported value |
| True claims labeled "hallucinated" / accuracy "factually incorrect" when no reference was available | Real user-submitted PDF reports | `verifiable` flag threaded from agents through to the Verdict Agent; four layers of regression tests |
| pandas 3.0's nullable string dtype breaking missing-value detection | Testing the CSV validator against a deliberately malformed file | Fill NA before stringifying instead of relying on `str(NaN) == "nan"` |
| `@app.on_event("startup")` not firing under a bare `TestClient`, silently masking a "table doesn't exist" risk | Writing the first history integration test | Schema creation made idempotent on every DB connection, not just at startup; also modernized to FastAPI's `lifespan` API |

## 5. Known Limitations (Honest Assessment)

- **Completeness scoring is keyword-based, not semantic** — a response
  can register "covers X" via surface keyword matches without genuinely
  discussing X in context. Documented, not hidden.
- **RAG relevance threshold (cosine distance ≤ 0.75) is a reasonable
  starting point, not empirically tuned** against the real embedding
  model at scale — worth revisiting with a larger, more diverse knowledge
  base.
- **Single-dimension endpoints** (`/evaluate/relevance`, `/accuracy`, etc.)
  deliberately do not get RAG fallback or history tagging — only the
  combined `/evaluate/all` and `/evaluate/verdict` do. Documented in the
  backend README as an intentional scoping decision, not an oversight.
- **No authentication** — appropriate for an academic/demo deployment,
  would need addressing before any real multi-user production use.

## 6. How to Run the Full Demo

1. `backend/README.md` — install, seed the knowledge base, start the API.
2. `frontend/README.md` — install, start Streamlit.
3. `pytest tests/ -v` in both `backend/` and `frontend/` — 73/73 should pass.
4. `TWO_SYSTEM_DEMO.md` — walkthrough for the two-AI-systems comparison demo.
