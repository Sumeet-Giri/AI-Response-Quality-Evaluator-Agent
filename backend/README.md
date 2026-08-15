# AI Response Quality Evaluator Agent — Backend

FastAPI backend for a multi-agent AI response evaluation system. Five
independent agents score an AI response on Relevance, Accuracy,
Hallucination, and Completeness; a Verdict Agent combines those into a
weighted overall score and a PASS/FAIL quality gate. Every evaluation is
persisted to SQLite automatically, powering the frontend Dashboard's
cross-batch trends and multi-system comparison.

## Structure

```
backend/
├── app/
│   ├── main.py                    FastAPI app, routers, lifespan startup, global error handling
│   ├── core/config.py             Paths / base config
│   ├── schemas/                   Pydantic models (request + all agent results)
│   ├── agents/                    The five evaluation agents
│   ├── orchestration/orchestrator.py   Runs the full pipeline in order; owns RAG fallback + history recording
│   ├── services/
│   │   ├── embedder.py / similarity.py      Shared embedding model + cosine similarity
│   │   ├── retriever.py / chroma_manager.py Reference-knowledge-base RAG lookup
│   │   ├── chunker.py / dataset_loader.py / squad_loader.py / truthfulqa_loader.py  RAG ingestion
│   │   └── history_store.py       SQLite persistence + aggregation queries for the Dashboard
│   ├── validation/                 Benchmark test cases + BenchmarkValidator
│   └── api/                        evaluate.py, validation.py, history.py routers
├── tests/                          pytest suite: agent logic, orchestration, and full E2E integration
├── scripts/                        Manual one-off scripts for inspecting the RAG pipeline
├── conftest.py                     Test-only fakes for sentence-transformers/chromadb
└── requirements.txt
```

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API comes up on `http://localhost:8000`. `GET /health` is a liveness check.
`evaluation_history.db` (SQLite) is created automatically on first startup.

## Seeding the reference knowledge base (for RAG fallback)

`/evaluate/all` and `/evaluate/verdict` use Retrieval-Augmented Generation
as a fallback: if you don't supply `reference_answer`, the orchestrator
retrieves the closest passage from a ChromaDB knowledge base (seeded from
TruthfulQA/SQuAD) and uses it instead — but only if it's actually close
enough to be useful (cosine distance ≤ 0.75); otherwise it degrades to "no
reference available" rather than handing back an irrelevant passage. The
collection is empty on a fresh checkout:

```bash
python scripts/test_chromadb.py
```

**When there's genuinely no reference and nothing relevant in the
knowledge base**, Accuracy and Hallucination are reported as
**"Unverified"** (`verifiable: false` in the response), not as
confirmed-wrong — the response still contributes conservatively to the
quality gate (unverified counts as a gate failure, same as before), but
the reasoning text and verdict weaknesses now say honestly that nothing
was checked, instead of asserting a factual problem that was never
actually detected. This distinction matters and is covered by dedicated
regression tests (`test_no_reference_never_labels_a_claim_as_hallucinated`,
`test_unverifiable_accuracy_and_hallucination_do_not_produce_false_weaknesses`).

## Running tests

```bash
pytest tests/ -v
```

52 tests across two categories:
- **Unit tests** (`test_relevance_agent.py`, `test_accuracy_agent.py`,
  `test_hallucination_agent.py`, `test_completeness.py`,
  `test_verdict_agent.py`, `test_validation.py`) — one agent's logic in
  isolation, exact assertions where the math is deterministic, relative
  comparisons where it depends on the embedding model.
- **End-to-end integration** (`test_e2e_integration.py`) — boots the real
  FastAPI app via `TestClient` and drives it exactly like the frontend
  does: HTTP in, JSON out, real orchestrator, real SQLite persistence,
  real validation. Covers input validation over HTTP, the full
  single-evaluation contract, RAG fallback firing and not firing, batch
  tagging actually persisting and being queryable back out through
  `/history/*`, the unverifiable-dimension fix holding together
  end-to-end, and clean error handling (no leaked tracebacks).

`conftest.py` injects lightweight deterministic fakes for
`sentence_transformers` and `chromadb` so the suite runs in seconds
without downloading model weights or standing up a real vector index. It
has no effect outside the test session — `uvicorn app.main:app` always
uses the real packages in `requirements.txt`.

## API

| Endpoint | Method | Notes |
|---|---|---|
| `/evaluate/relevance` `/accuracy` `/hallucination` `/completeness` | POST | Single-dimension scoring (no RAG fallback — see note below). |
| `/evaluate/verdict` | POST | Full pipeline, returns just the verdict. |
| `/evaluate/all` | POST | Full pipeline: every agent's result + verdict + RAG metadata. Automatically recorded to history. |
| `/validation/relevance` `/accuracy` `/hallucination` `/completeness` `/all` | GET | Runs each agent against its fixed benchmark cases. |
| `/history/summary` | GET | Aggregate stats across every evaluation ever recorded. |
| `/history/batches` | GET | One row per batch run — the Dashboard's "trends across batch evaluations" source. |
| `/history/systems` | GET | One row per tagged `system_name` — the Dashboard's system-comparison source. |
| `/history/runs` | GET | Raw rows, filterable by `system_name` / `batch_id` / `mode`. |
| `/health` | GET | Liveness check. |

Request body for every `/evaluate/*` endpoint:
```json
{
  "question": "string, required, non-blank",
  "response": "string, required, non-blank",
  "reference_answer": "string, optional -- if omitted, RAG fallback is used",
  "system_name": "string, optional, default 'Unspecified' -- tags this evaluation for the Dashboard",
  "batch_id": "string, optional -- groups rows from one batch run together",
  "batch_label": "string, optional -- human-readable label for a batch run"
}
```

Note: RAG fallback and history-tagging both apply to `/evaluate/all` and
`/evaluate/verdict` only, not the single-dimension endpoints — this is a
deliberate scoping choice (see the comment at the top of `app/api/evaluate.py`)
so single-dimension results stay simple and predictable rather than
behaving inconsistently with the combined endpoint for the same input.
