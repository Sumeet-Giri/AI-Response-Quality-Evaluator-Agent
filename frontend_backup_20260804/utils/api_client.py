"""
API Client
----------
Thin wrapper around the FastAPI backend. IMPORTANT: this file does not
change or reinterpret any backend logic — it only calls the existing
endpoints exactly as documented (/evaluate/relevance, /evaluate/accuracy,
/evaluate/hallucination, /evaluate/completeness, /evaluate/verdict,
/evaluate/all) and returns the raw JSON payloads untouched.

A MOCK_MODE fallback is included purely so the redesigned frontend can be
demoed / screenshotted before the backend is running, or during a live
presentation if the backend connection drops. It is never used when the
real backend responds successfully.
"""

import os
import requests
import random

BACKEND_URL = os.getenv("EVAL_BACKEND_URL", "http://localhost:8000")
TIMEOUT = 30


class BackendUnavailable(Exception):
    pass


def _post(endpoint: str, payload: dict) -> dict:
    url = f"{BACKEND_URL}{endpoint}"
    resp = requests.post(url, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _mock_payload(kind: str) -> dict:
    """Deterministic-ish mock responses matching the documented schema shapes.
    Used ONLY when the backend cannot be reached, so the UI is always demoable."""
    if kind == "relevance":
        return {
            "score": round(random.uniform(6.5, 9.5), 1),
            "semantic_similarity": round(random.uniform(0.7, 0.95), 2),
            "topic_match": True,
            "reasoning": "The response directly addresses the core question and stays on-topic "
                         "throughout, with only minor tangents.",
        }
    if kind == "accuracy":
        return {
            "score": round(random.uniform(6.0, 9.3), 1),
            "semantic_similarity": round(random.uniform(0.65, 0.92), 2),
            "factually_correct": True,
            "evidence": ["Matches reference answer on key facts", "No contradicting claims found"],
            "reasoning": "Core factual claims align with the reference answer; no contradictions detected.",
        }
    if kind == "hallucination":
        return {
            "score": round(random.uniform(7.0, 9.8), 1),
            "supported_claims": ["Claim A is backed by the source context", "Claim B matches known facts"],
            "hallucinated_claims": [] if random.random() > 0.3 else ["Unverified claim about a statistic"],
            "reasoning": "Most claims are traceable to supporting context; minimal unsupported content.",
        }
    if kind == "completeness":
        total = 5
        covered = random.randint(3, 5)
        return {
            "score": round(covered / total * 10, 1),
            "coverage_percentage": round(covered / total * 100, 1),
            "total_aspects": total,
            "extracted_aspects": ["Definition", "Cause", "Effect", "Example", "Limitation"],
            "covered_aspects": ["Definition", "Cause", "Effect"][:covered],
            "missing_aspects": ["Example", "Limitation"][: max(0, total - covered)],
            "reasoning": "Response covers the primary aspects of the question but omits some supporting detail.",
        }
    if kind == "verdict":
        return {
            "overall_score": round(random.uniform(7.0, 9.0), 1),
            "final_verdict": "High Quality",
            "quality_gate_passed": True,
            "weighted_score_breakdown": {
                "relevance": round(random.uniform(6.5, 9.5), 1),
                "accuracy": round(random.uniform(6.0, 9.3), 1),
                "hallucination": round(random.uniform(7.0, 9.8), 1),
                "completeness": round(random.uniform(6.0, 9.0), 1),
            },
            "strengths": ["Strong topical relevance", "Low hallucination risk", "Factually consistent"],
            "weaknesses": ["Some supporting detail missing"],
            "consolidated_reasoning": "Overall the response is relevant, accurate, and largely complete, "
                                      "with low hallucination risk.",
        }
    return {}


def evaluate_dimension(dimension: str, question: str, response: str, reference: str = "") -> tuple[dict, bool]:
    """
    Calls POST /evaluate/{dimension}.
    Returns (data, used_mock).
    """
    payload = {"question": question, "response": response, "reference_answer": reference}
    try:
        return _post(f"/evaluate/{dimension}", payload), False
    except Exception:
        return _mock_payload(dimension), True


def evaluate_all(question: str, response: str, reference: str = "") -> tuple[dict, bool]:
    """
    Calls POST /evaluate/all. Returns (data, used_mock).
    """
    payload = {"question": question, "response": response, "reference_answer": reference}
    try:
        return _post("/evaluate/all", payload), False
    except Exception:
        return {
            "relevance": _mock_payload("relevance"),
            "accuracy": _mock_payload("accuracy"),
            "hallucination": _mock_payload("hallucination"),
            "completeness": _mock_payload("completeness"),
            "verdict": _mock_payload("verdict"),
        }, True


def backend_health() -> bool:
    try:
        r = requests.get(f"{BACKEND_URL}/", timeout=3)
        return r.status_code < 500
    except Exception:
        return False
