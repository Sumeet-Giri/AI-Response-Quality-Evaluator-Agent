"""
End-to-End tests for the Single Evaluation page (Milestone 4, item 3).

Drives the REAL page through Streamlit's AppTest -- filling in the actual
text inputs, clicking the actual "Evaluate Response" button, and reading
back the actual rendered widgets -- with api_client mocked at the `_post`
layer so no live backend is needed. Mocking at `_post` (not `evaluate_all`
itself) is deliberate: an earlier round of manual testing this session
mocked `evaluate_all` directly and, as a result, completely missed a real
bug in `_normalize_all()` that silently dropped the "rag" key. Mocking one
layer lower closes that gap for good.
"""

import os
import pathlib

import pytest
from streamlit.testing.v1 import AppTest

import utils.api_client as api_client

HARNESS = str(pathlib.Path(__file__).parent / "_harness_single_evaluation.py")


def _run_with_response(monkeypatch, backend_response, question="What is the capital of France?",
                        response_text="Paris is the capital of France.", system_name="GPT-4"):
    monkeypatch.setattr(api_client, "_post", lambda endpoint, payload: backend_response)
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    at.text_area[0].set_value(question)
    at.text_area[1].set_value(response_text)
    at.text_input[0].set_value(system_name)
    [b for b in at.button if "Evaluate" in b.label][0].click().run()
    return at


VERIFIED_RESPONSE = {
    "relevance": {"score": 10, "semantic_similarity": 0.95, "topic_match": True, "reasoning": "Directly answers the question."},
    "accuracy": {"score": 10, "semantic_similarity": 0.97, "factually_correct": True, "verifiable": True,
                 "evidence": ["Paris is the capital of France."], "reasoning": "Matches the reference answer."},
    "hallucination": {"hallucination_score": 10, "supported_claims": ["Paris is the capital of France"],
                       "hallucinated_claims": [], "total_claims": 1, "supported_claims_count": 1,
                       "hallucinated_claims_count": 0, "hallucination_rate": 0.0, "verifiable": True,
                       "reasoning": "No hallucinations were detected."},
    "completeness": {"completeness_score": 10, "coverage_percentage": 100.0, "total_aspects": 1,
                      "extracted_aspects": ["Definition"], "covered_aspects": ["Definition"], "missing_aspects": [],
                      "reasoning": "Fully covers the question."},
    "verdict": {"overall_score": 10.0, "final_verdict": "EXCELLENT", "quality_gate_passed": True,
                "failed_conditions": [], "weighted_breakdown": {"relevance": 2.5, "accuracy": 3.5,
                "hallucination": 2.5, "completeness": 1.5},
                "strengths": ["The response is highly relevant to the question.", "The response is factually accurate.",
                              "No hallucinated or unsupported claims were detected.",
                              "The response provides comprehensive coverage."],
                "weaknesses": [], "consolidated_reasoning": "..."},
    "rag": {"source": "user_supplied"},
}

UNVERIFIABLE_RESPONSE = {
    "relevance": {"score": 6, "semantic_similarity": 0.68, "topic_match": True, "reasoning": "Moderately relevant."},
    "accuracy": {"score": 0, "semantic_similarity": 0.0, "factually_correct": False, "verifiable": False,
                 "evidence": [], "reasoning": "Accuracy could not be verified: no reference answer or retrieved "
                 "evidence was available for comparison. This is NOT a determination that the response is incorrect."},
    "hallucination": {"hallucination_score": 0, "supported_claims": [], "hallucinated_claims": [],
                       "total_claims": 0, "supported_claims_count": 0, "hallucinated_claims_count": 0,
                       "hallucination_rate": 0.0, "verifiable": False,
                       "reasoning": "Hallucination could not be assessed: no reference answer or retrieved evidence "
                       "was available for comparison. This is NOT a determination that the response contains hallucinations."},
    "completeness": {"completeness_score": 10, "coverage_percentage": 100.0, "total_aspects": 1,
                      "extracted_aspects": ["Definition"], "covered_aspects": ["Definition"], "missing_aspects": [],
                      "reasoning": "Covers the definition."},
    "verdict": {"overall_score": 3.0, "final_verdict": "FAIL", "quality_gate_passed": False,
                "failed_conditions": ["Accuracy could not be verified...", "Hallucination risk could not be assessed..."],
                "weighted_breakdown": {"relevance": 1.5, "accuracy": 0.0, "hallucination": 0.0, "completeness": 1.5},
                "strengths": ["The response provides comprehensive coverage."],
                "weaknesses": ["The response could be more relevant to the question.",
                               "Accuracy could not be verified -- no reference answer or retrieved evidence was "
                               "available for comparison.",
                               "Hallucination risk could not be assessed -- no reference answer or retrieved "
                               "evidence was available for comparison."],
                "consolidated_reasoning": "..."},
    "rag": {"source": "none", "reason": "..."},
}

# Regression fixture: a real negative cosine similarity, which previously
# crashed st.progress() because only the upper bound was clamped.
NEGATIVE_SIMILARITY_RESPONSE = {
    **UNVERIFIABLE_RESPONSE,
    "accuracy": {**UNVERIFIABLE_RESPONSE["accuracy"], "semantic_similarity": -0.0403, "verifiable": True,
                 "reasoning": "The response is factually incorrect."},
}


def test_page_renders_with_no_input(monkeypatch):
    monkeypatch.setattr(api_client, "_post", lambda endpoint, payload: VERIFIED_RESPONSE)
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    assert not at.exception


def test_empty_input_shows_warning_not_crash(monkeypatch):
    monkeypatch.setattr(api_client, "_post", lambda endpoint, payload: VERIFIED_RESPONSE)
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    [b for b in at.button if "Evaluate" in b.label][0].click().run()
    assert not at.exception
    assert len(at.warning) >= 1


def test_full_evaluation_flow_renders_all_pipeline_stages(monkeypatch):
    at = _run_with_response(monkeypatch, VERIFIED_RESPONSE)
    assert not at.exception
    markdown_text = " ".join(m.value for m in at.markdown)
    for stage in ["Relevance", "Accuracy", "Hallucination", "Completeness", "Verdict"]:
        assert stage in markdown_text


def test_pdf_download_button_present_after_evaluation(monkeypatch):
    at = _run_with_response(monkeypatch, VERIFIED_RESPONSE)
    pdf_buttons = [d for d in at.get("download_button") if "PDF" in d.label]
    assert len(pdf_buttons) == 1


def test_unverifiable_case_shows_neutral_badges_not_false_negatives(monkeypatch):
    at = _run_with_response(
        monkeypatch, UNVERIFIABLE_RESPONSE,
        question="what is capital of india", response_text="New Delhi is the capital of India.",
    )
    assert not at.exception
    markdown_text = " ".join(m.value for m in at.markdown)
    warnings = [w.value for w in at.warning]

    assert "Unverified" in markdown_text
    assert "Factual Issues Found" not in markdown_text
    assert any("No reference answer was supplied" in w for w in warnings)


def test_negative_similarity_does_not_crash_the_progress_bar(monkeypatch):
    # Regression test for a real reported crash: st.progress() rejects
    # values outside [0.0, 1.0], and cosine similarity can legitimately
    # go negative.
    at = _run_with_response(
        monkeypatch, NEGATIVE_SIMILARITY_RESPONSE,
        question="what is capital of india",
        response_text="A long detailed response with no reference to compare against.",
    )
    assert not at.exception


def test_backend_unreachable_falls_back_to_demo_mode_without_crashing(monkeypatch):
    def raise_connection_error(endpoint, payload):
        raise ConnectionError("backend unreachable")
    monkeypatch.setattr(api_client, "_post", raise_connection_error)

    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    at.text_area[0].set_value("What is the capital of France?")
    at.text_area[1].set_value("Paris is the capital of France.")
    [b for b in at.button if "Evaluate" in b.label][0].click().run()
    assert not at.exception
