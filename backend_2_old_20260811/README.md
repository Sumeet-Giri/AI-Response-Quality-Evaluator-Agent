# AI Response Quality Evaluator Agent — Backend

FastAPI backend for a multi-agent AI response evaluation system. Five
independent agents score an AI response on Relevance, Accuracy,
Hallucination, and Completeness; a Verdict Agent combines those into a
weighted overall score and a PASS/FAIL quality gate.

## Structure

```
backend/
├── app/
│   ├── main.py                    FastAPI app, routers, global error handling
│   ├── core/config.py             Paths / base config
│   ├── schemas/                   Pydantic models (request + all agent results)
│   ├── agents/                    The five evaluation agents
│   ├── orchestration/orchestrator.py   Runs the full pipeline in order; owns RAG fallback
│   ├── services/                  Embeddings, similarity, RAG (retriever/chroma/chunker/loaders)
│   ├── validation/                Benchmark test cases + BenchmarkValidator
│   └── api/                       evaluate.py, validation.py routers
├── tests/                         pytest suite (agent logic + orchestration)
├── scripts/                       Manual one-off scripts for inspecting the RAG pipeline
├── conftest.py                    Test-only fakes for sentence-transformers/chromadb
└── requirements.txt
```

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API comes up on `http://localhost:8000`. `GET /health` is a liveness check.

## Seeding the reference knowledge base (for RAG fallback)

`/evaluate/all` and `/evaluate/verdict` use Retrieval-Augmented Generation
as a fallback: if you don't supply `reference_answer` in the request, the
orchestrator retrieves the closest passage from a ChromaDB knowledge base
(seeded from TruthfulQA/SQuAD) and uses that instead. The collection is
empty on a fresh checkout. To seed it:

```bash
python scripts/test_chromadb.py
```

Until it's seeded, RAG fallback degrades gracefully — Accuracy and
Hallucination score with an empty reference, exactly as they did before
RAG was wired in — rather than failing the request.

## Running tests

```bash
pytest tests/ -v
```

`conftest.py` injects lightweight deterministic fakes for
`sentence_transformers` and `chromadb` so the suite runs in seconds without
downloading model weights or standing up a real vector index. It has no
effect outside the test session.

## API

| Endpoint | Method | Notes |
|---|---|---|
| `/evaluate/relevance` `/accuracy` `/hallucination` `/completeness` | POST | Single-dimension scoring. |
| `/evaluate/verdict` | POST | Full pipeline, returns just the verdict. |
| `/evaluate/all` | POST | Full pipeline, returns every agent's result + verdict + RAG metadata. |
| `/validation/relevance` `/accuracy` `/hallucination` `/completeness` `/all` | GET | Runs each agent against its fixed benchmark cases. |
| `/health` | GET | Liveness check. |

Request body for every `/evaluate/*` endpoint:
```json
{
  "question": "string, required, non-blank",
  "response": "string, required, non-blank",
  "reference_answer": "string, optional -- if omitted, RAG fallback is used"
}
```
