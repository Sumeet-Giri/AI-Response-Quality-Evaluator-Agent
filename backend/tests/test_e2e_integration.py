"""
End-to-End Integration Tests (Milestone 4, item 3)
-----------------------------------------------------
Unlike the other files in tests/ (which exercise one agent's logic in
isolation), this file boots the REAL FastAPI app via TestClient and drives
it exactly the way the frontend does: HTTP requests in, JSON responses out,
with the real orchestrator, real SQLite persistence, and real validation
all wired together. Only the heavy ML/vector-DB libraries are faked (see
conftest.py) -- everything else in this file is the genuine request path.

Covers what the individual agent tests can't:
- Input validation actually rejecting bad requests over HTTP (422s)
- The full single-evaluation request/response contract
- RAG fallback actually firing (and not firing) end-to-end
- Batch-style tagging (system_name/batch_id) actually persisting and
  actually being queryable back out through /history/*
- The "unverifiable" fix holding together across the whole stack: agent
  reasoning -> verdict weaknesses -> the exact JSON the frontend/PDF read
- Quality-gate / verdict math staying correct through the full pipeline
- Clean error handling for unexpected failures (no leaked tracebacks)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


# --------------------------------------------------------------------
# Input validation over the real HTTP boundary
# --------------------------------------------------------------------

def test_empty_question_is_rejected_with_422(client):
    r = client.post("/evaluate/all", json={
        "question": "   ", "response": "something", "reference_answer": "",
    })
    assert r.status_code == 422
    assert r.json()["error"] == "validation_error"


def test_missing_required_field_is_rejected_with_422(client):
    r = client.post("/evaluate/all", json={"response": "something"})
    assert r.status_code == 422


def test_valid_request_is_accepted(client):
    r = client.post("/evaluate/all", json={
        "question": "What is the capital of France?",
        "response": "Paris is the capital of France.",
        "reference_answer": "Paris is the capital of France.",
    })
    assert r.status_code == 200


# --------------------------------------------------------------------
# Full single-evaluation contract
# --------------------------------------------------------------------

def test_evaluate_all_returns_every_expected_section(client):
    r = client.post("/evaluate/all", json={
        "question": "What is the capital of France?",
        "response": "Paris is the capital of France.",
        "reference_answer": "Paris is the capital of France.",
    })
    data = r.json()
    assert set(data.keys()) == {"relevance", "accuracy", "hallucination", "completeness", "verdict", "rag"}
    for dim in ("relevance", "accuracy", "hallucination", "completeness"):
        assert "reasoning" in data[dim]
    assert "overall_score" in data["verdict"]
    assert "weighted_breakdown" in data["verdict"]


def test_matching_response_passes_quality_gate(client):
    r = client.post("/evaluate/all", json={
        "question": "What is the capital of France?",
        "response": "Paris is the capital of France.",
        "reference_answer": "Paris is the capital of France.",
    })
    verdict = r.json()["verdict"]
    assert verdict["quality_gate_passed"] is True
    assert verdict["overall_score"] >= 8


def test_evaluate_verdict_endpoint_returns_only_the_verdict_shape(client):
    r = client.post("/evaluate/verdict", json={
        "question": "What is the capital of France?",
        "response": "Paris is the capital of France.",
        "reference_answer": "Paris is the capital of France.",
    })
    data = r.json()
    assert set(data.keys()) == {
        "overall_score", "final_verdict", "quality_gate_passed", "failed_conditions",
        "weighted_breakdown", "strengths", "weaknesses", "consolidated_reasoning",
    }


# --------------------------------------------------------------------
# The "unverifiable" fix, end-to-end (agents -> verdict -> JSON)
# --------------------------------------------------------------------

def test_unverifiable_dimensions_produce_honest_text_not_false_claims(client):
    r = client.post("/evaluate/all", json={
        "question": "what is capital of india",
        "response": "New Delhi is the capital of India.",
        "reference_answer": "",
    })
    data = r.json()

    assert data["hallucination"]["hallucinated_claims"] == []
    assert "could not be verified" in data["accuracy"]["reasoning"].lower()
    assert "could not be assessed" in data["hallucination"]["reasoning"].lower()
    assert "factually incorrect" not in data["accuracy"]["reasoning"].lower()

    weaknesses = data["verdict"]["weaknesses"]
    assert not any("factual correctness of the response could be improved" in w for w in weaknesses)
    assert not any("claims may lack sufficient factual support" in w for w in weaknesses)
    assert any("could not be verified" in w.lower() for w in weaknesses)

    # Still conservatively fails -- only the wording changed, not the outcome.
    assert data["verdict"]["quality_gate_passed"] is False
    assert data["verdict"]["final_verdict"] == "FAIL"


def test_rag_fallback_does_not_fire_when_reference_is_supplied(client):
    r = client.post("/evaluate/all", json={
        "question": "What is the capital of France?",
        "response": "Paris is the capital of France.",
        "reference_answer": "Paris is the capital of France.",
    })
    assert r.json()["rag"]["source"] == "user_supplied"


def test_rag_fallback_degrades_gracefully_when_kb_is_empty(client):
    r = client.post("/evaluate/all", json={
        "question": "A question nothing in an empty KB could match.",
        "response": "Some response.",
        "reference_answer": "",
    })
    assert r.json()["rag"]["source"] == "none"


# --------------------------------------------------------------------
# System tagging + history persistence, fully wired
# --------------------------------------------------------------------

def test_tagged_evaluations_are_queryable_back_out_by_system(client):
    for i in range(3):
        r = client.post("/evaluate/all", json={
            "question": f"Q{i}", "response": f"A{i}", "reference_answer": f"A{i}",
            "system_name": "IntegrationTestSystem",
        })
        assert r.status_code == 200

    runs = client.get("/history/runs", params={"system_name": "IntegrationTestSystem"}).json()
    assert len(runs) >= 3
    assert all(run["system_name"] == "IntegrationTestSystem" for run in runs)

    systems = client.get("/history/systems").json()
    tagged = next(s for s in systems if s["system_name"] == "IntegrationTestSystem")
    assert tagged["total_evaluations"] >= 3


def test_batch_tagged_rows_are_grouped_under_one_batch_id(client):
    batch_id = "e2e-test-batch-001"
    for i in range(4):
        r = client.post("/evaluate/all", json={
            "question": f"BatchQ{i}", "response": f"BatchA{i}", "reference_answer": f"BatchA{i}",
            "system_name": "BatchTestSystem", "batch_id": batch_id, "batch_label": "E2E test batch",
        })
        assert r.status_code == 200

    batches = client.get("/history/batches").json()
    this_batch = next(b for b in batches if b["batch_id"] == batch_id)
    assert this_batch["row_count"] == 4
    assert this_batch["batch_label"] == "E2E test batch"
    assert this_batch["system_name"] == "BatchTestSystem"


def test_history_summary_reflects_recorded_evaluations(client):
    before = client.get("/history/summary").json()["total_evaluations"] or 0
    client.post("/evaluate/all", json={
        "question": "Summary check Q", "response": "Summary check A",
        "reference_answer": "Summary check A",
    })
    after = client.get("/history/summary").json()["total_evaluations"]
    assert after == before + 1


# --------------------------------------------------------------------
# Validation endpoints (benchmark cases)
# --------------------------------------------------------------------

def test_validation_all_covers_every_agent(client):
    r = client.get("/validation/all")
    data = r.json()
    assert set(data.keys()) == {
        "relevance_validation", "accuracy_validation",
        "hallucination_validation", "completeness_validation",
    }
    for key in data:
        assert len(data[key]) > 0


# --------------------------------------------------------------------
# Health & error handling
# --------------------------------------------------------------------

def test_health_check(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_unhandled_error_returns_clean_json_not_a_raw_traceback():
    with TestClient(app, raise_server_exceptions=False) as c:
        import app.api.evaluate as evaluate_module
        original = evaluate_module.EvaluationOrchestrator

        class BoomOrchestrator(original):
            def run_all(self, *a, **kw):
                raise RuntimeError("simulated internal failure")

        evaluate_module.EvaluationOrchestrator = BoomOrchestrator
        try:
            r = c.post("/evaluate/all", json={
                "question": "q", "response": "r", "reference_answer": "ref",
            })
        finally:
            evaluate_module.EvaluationOrchestrator = original

        assert r.status_code == 500
        assert r.json()["error"] == "internal_server_error"
        assert "RuntimeError" not in r.text
        assert "Traceback" not in r.text
