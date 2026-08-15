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

# A pooled session (instead of a fresh connection per call) meaningfully cuts
# per-request overhead when this client is used in a loop, e.g. batch
# evaluation of many CSV rows against /evaluate/all.
_SESSION = requests.Session()


class BackendUnavailable(Exception):
    pass


def _post(endpoint: str, payload: dict) -> dict:
    url = f"{BACKEND_URL}{endpoint}"
    resp = _SESSION.post(url, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


# --------------------------------------------------------------------------
# Backward-compatible normalization
# --------------------------------------------------------------------------
# The real backend's Pydantic models use dimension-specific field names
# (hallucination_score, completeness_score) and VerdictResult.weighted_breakdown,
# while the rest of this frontend (result_cards.py, single_evaluation.py) was
# written against a generic `score` key and `weighted_score_breakdown`. That
# mismatch meant real (non-mock) responses rendered as 0 / empty in the UI.
#
# These helpers ADD the expected aliases alongside the original keys — they
# never remove or rewrite anything the backend sent, so nothing downstream
# breaks; pages that already read the original field names keep working, and
# pages that read the generic aliases now get real data too.
def _normalize_dimension(kind: str, data: dict) -> dict:
    if not isinstance(data, dict):
        return data
    if kind == "hallucination" and "score" not in data and "hallucination_score" in data:
        data = {**data, "score": data["hallucination_score"]}
    elif kind == "completeness" and "score" not in data and "completeness_score" in data:
        data = {**data, "score": data["completeness_score"]}
    return data


def _normalize_verdict(data: dict) -> dict:
    if not isinstance(data, dict):
        return data
    if "weighted_score_breakdown" not in data and "weighted_breakdown" in data:
        data = {**data, "weighted_score_breakdown": data["weighted_breakdown"]}
    return data


def _normalize_all(data: dict) -> dict:
    if not isinstance(data, dict):
        return data
    return {
        "relevance": _normalize_dimension("relevance", data.get("relevance", {})),
        "accuracy": _normalize_dimension("accuracy", data.get("accuracy", {})),
        "hallucination": _normalize_dimension("hallucination", data.get("hallucination", {})),
        "completeness": _normalize_dimension("completeness", data.get("completeness", {})),
        "verdict": _normalize_verdict(data.get("verdict", {})),
        # BUG FIX: this key was previously dropped entirely because this
        # function rebuilds a fresh dict with only the 5 keys above. That
        # silently broke the RAG-transparency warning on Single Evaluation
        # (it was always rendering with rag_info=None) and meant PDF
        # reports never explained *why* Accuracy/Hallucination scored 0
        # when no reference was available -- it just looked like a
        # correct answer and a wrong answer scoring identically for no
        # visible reason. Found via a real user report, not caught by
        # testing because the test mocked evaluate_all() directly instead
        # of exercising this normalization function.
        "rag": data.get("rag", {}),
    }


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
        return _normalize_dimension(dimension, _post(f"/evaluate/{dimension}", payload)), False
    except Exception:
        return _normalize_dimension(dimension, _mock_payload(dimension)), True


def evaluate_all(
    question: str,
    response: str,
    reference: str = "",
    system_name: str = "Unspecified",
    batch_id: str | None = None,
    batch_label: str | None = None,
) -> tuple[dict, bool]:
    """
    Calls POST /evaluate/all. Returns (data, used_mock).

    system_name / batch_id / batch_label are optional tagging metadata for
    the evaluation history the Dashboard reads from -- they don't affect
    scoring at all. Omit them for an untagged single evaluation.
    """
    payload = {
        "question": question,
        "response": response,
        "reference_answer": reference,
        "system_name": system_name,
    }
    if batch_id:
        payload["batch_id"] = batch_id
        payload["batch_label"] = batch_label
    try:
        return _normalize_all(_post("/evaluate/all", payload)), False
    except Exception:
        return _normalize_all({
            "relevance": _mock_payload("relevance"),
            "accuracy": _mock_payload("accuracy"),
            "hallucination": _mock_payload("hallucination"),
            "completeness": _mock_payload("completeness"),
            "verdict": _mock_payload("verdict"),
        }), True


def backend_health() -> bool:
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


# --------------------------------------------------------------------------
# Evaluation history / Dashboard (Milestone 4)
# --------------------------------------------------------------------------
# These read from the SQLite-backed history that EvaluationOrchestrator
# writes to automatically on every /evaluate/all call. If the backend is
# unreachable, each function returns an empty/zeroed result rather than
# raising, so the Dashboard page can render a clear "no data" state instead
# of crashing.

def get_history_summary() -> dict:
    try:
        r = _SESSION.get(f"{BACKEND_URL}/history/summary", timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


def get_batch_summaries(limit: int = 100) -> list[dict]:
    try:
        r = _SESSION.get(f"{BACKEND_URL}/history/batches", params={"limit": limit}, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def get_system_summaries() -> list[dict]:
    try:
        r = _SESSION.get(f"{BACKEND_URL}/history/systems", timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def get_history_runs(system_name: str = None, batch_id: str = None, mode: str = None, limit: int = 500) -> list[dict]:
    params = {"limit": limit}
    if system_name:
        params["system_name"] = system_name
    if batch_id:
        params["batch_id"] = batch_id
    if mode:
        params["mode"] = mode
    try:
        r = _SESSION.get(f"{BACKEND_URL}/history/runs", params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []
