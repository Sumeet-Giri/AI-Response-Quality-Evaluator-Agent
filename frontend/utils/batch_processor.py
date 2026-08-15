"""
Batch Processor
----------------
Business logic for running the multi-agent pipeline across every row of a
validated CSV. Deliberately kept separate from Streamlit — no `st.*` calls
in here — so it stays testable and reusable.

Reuses utils.api_client.evaluate_all exactly as-is (POST /evaluate/all),
per row. No new backend endpoint is introduced: the spec's own fallback
instruction ("otherwise reuse /evaluate/all") applies here since a single
extra endpoint isn't needed for correctness — only for backend-side batching
performance, which is a Milestone 2 concern.
"""

import time
import uuid
from typing import Callable, Optional

import pandas as pd

from utils.api_client import evaluate_all

REQUIRED_COLUMNS = ["question", "response"]


def _truncate(text: str, n: int = 90) -> str:
    text = text or ""
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def run_batch(
    df: pd.DataFrame,
    progress_callback: Optional[Callable[[int, int, float, float], None]] = None,
    system_name: str = "Unspecified",
    batch_label: Optional[str] = None,
    batch_id: Optional[str] = None,
) -> dict:
    """
    Runs POST /evaluate/all sequentially for every row in `df`.

    progress_callback(done, total, elapsed_seconds, estimated_remaining_seconds)
    is invoked after every row so the UI can update a progress bar / ETA text.

    system_name / batch_label / batch_id tag every row of this run so it's
    grouped together and attributed to a specific AI system on the
    Dashboard (Milestone 4). A batch_id is auto-generated if not supplied
    -- one call to run_batch() is always exactly one batch in history,
    regardless of how many rows it contains.

    Returns a dict:
        {
            "table": pd.DataFrame        # one row per input row, flattened scores
            "full_rows": list[dict]      # full nested per-row API payload (for JSON export / drill-down)
            "errors": list[dict]         # rows that raised an exception
            "used_mock": bool            # True if ANY row fell back to demo data
            "total_time": float
            "batch_id": str
        }
    """
    n = len(df)
    table_rows = []
    full_rows = []
    errors = []
    used_mock_any = False
    batch_id = batch_id or uuid.uuid4().hex[:12]

    start_time = time.time()

    for pos in range(n):
        row = df.iloc[pos]
        question = str(row.get("question", "")).strip()
        response_text = str(row.get("response", "")).strip()
        reference = str(row.get("reference_answer", "")).strip()
        if reference.lower() in ("nan", "none", "null"):
            reference = ""

        try:
            data, used_mock = evaluate_all(
                question, response_text, reference,
                system_name=system_name,
                batch_id=batch_id,
                batch_label=batch_label,
            )
            used_mock_any = used_mock_any or used_mock

            relevance = data.get("relevance", {}) or {}
            accuracy = data.get("accuracy", {}) or {}
            hallucination = data.get("hallucination", {}) or {}
            completeness = data.get("completeness", {}) or {}
            verdict = data.get("verdict", {}) or {}

            passed = bool(verdict.get("quality_gate_passed", False))

            table_rows.append({
                "#": pos + 1,
                "question": _truncate(question, 70),
                "response_preview": _truncate(response_text, 90),
                "relevance": relevance.get("score"),
                "accuracy": accuracy.get("score"),
                "hallucination": hallucination.get("score"),
                "completeness": completeness.get("score"),
                "overall_score": verdict.get("overall_score"),
                "final_verdict": verdict.get("final_verdict", "—"),
                "pass_fail": "PASS" if passed else "FAIL",
                "error": "",
            })
            full_rows.append({
                "row": pos + 1,
                "question": question,
                "response": response_text,
                "reference_answer": reference,
                **data,
            })

        except Exception as e:
            errors.append({"row": pos + 1, "question": _truncate(question, 90), "error": str(e)})
            table_rows.append({
                "#": pos + 1,
                "question": _truncate(question, 70),
                "response_preview": _truncate(response_text, 90),
                "relevance": None,
                "accuracy": None,
                "hallucination": None,
                "completeness": None,
                "overall_score": None,
                "final_verdict": "ERROR",
                "pass_fail": "ERROR",
                "error": str(e),
            })
            full_rows.append({
                "row": pos + 1,
                "question": question,
                "response": response_text,
                "reference_answer": reference,
                "error": str(e),
            })

        elapsed = time.time() - start_time
        avg_per_row = elapsed / (pos + 1)
        remaining = max(0.0, avg_per_row * (n - pos - 1))

        if progress_callback:
            progress_callback(pos + 1, n, elapsed, remaining)

    return {
        "table": pd.DataFrame(table_rows),
        "full_rows": full_rows,
        "errors": errors,
        "used_mock": used_mock_any,
        "total_time": time.time() - start_time,
        "batch_id": batch_id,
    }
