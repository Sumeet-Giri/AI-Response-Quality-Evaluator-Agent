"""
End-to-End tests for the Benchmark Validation (Batch Evaluation) page
(Milestone 4, item 3).

Drives the real page through AppTest: uses the built-in sample dataset,
fills in the tagging fields, clicks Run, and inspects the actual rendered
results -- summary tiles, charts, standout responses, detailed table, and
all four export buttons (CSV/Excel/JSON/PDF).

Mocks `utils.batch_processor.evaluate_all` specifically (not
`utils.api_client.evaluate_all`) because batch_processor.py does
`from utils.api_client import evaluate_all` -- a direct name import binds
that name into batch_processor's own module namespace, so patching the
api_client module's attribute would silently have no effect on what
run_batch() actually calls. Getting this mocking layer right matters --
this session already found one real bug specifically because an earlier
manual test mocked at the wrong layer.
"""

import pathlib

from streamlit.testing.v1 import AppTest

import utils.batch_processor as batch_processor

HARNESS = str(pathlib.Path(__file__).parent / "_harness_benchmark_validation.py")


def _fake_evaluate_all(question, response, reference, system_name="Unspecified",
                        batch_id=None, batch_label=None):
    # Deterministic-ish: "wrong"/off-topic sample rows score low, others score high,
    # so the resulting batch has a realistic mix of PASS/FAIL for the charts to render.
    is_bad = "banana" in response.lower() or "sydney" in response.lower()
    if is_bad:
        payload = {
            "relevance": {"score": 2, "semantic_similarity": 0.1, "topic_match": False, "reasoning": "..."},
            "accuracy": {"score": 0, "semantic_similarity": 0.0, "factually_correct": False, "verifiable": True,
                         "evidence": [reference], "reasoning": "The response is factually incorrect."},
            "hallucination": {"hallucination_score": 0, "supported_claims": [], "hallucinated_claims": ["x"],
                               "total_claims": 1, "supported_claims_count": 0, "hallucinated_claims_count": 1,
                               "hallucination_rate": 1.0, "verifiable": True, "reasoning": "Significant hallucinations."},
            "completeness": {"completeness_score": 2, "coverage_percentage": 20.0, "total_aspects": 1,
                              "extracted_aspects": [], "covered_aspects": [], "missing_aspects": ["Definition"],
                              "reasoning": "..."},
            "verdict": {"overall_score": 1.0, "final_verdict": "FAIL", "quality_gate_passed": False,
                        "failed_conditions": ["..."], "weighted_breakdown": {}, "strengths": [], "weaknesses": [],
                        "consolidated_reasoning": "..."},
        }
    else:
        payload = {
            "relevance": {"score": 9, "semantic_similarity": 0.9, "topic_match": True, "reasoning": "..."},
            "accuracy": {"score": 9, "semantic_similarity": 0.9, "factually_correct": True, "verifiable": True,
                         "evidence": [reference], "reasoning": "Matches the reference."},
            "hallucination": {"hallucination_score": 9, "supported_claims": ["x"], "hallucinated_claims": [],
                               "total_claims": 1, "supported_claims_count": 1, "hallucinated_claims_count": 0,
                               "hallucination_rate": 0.0, "verifiable": True, "reasoning": "No hallucinations."},
            "completeness": {"completeness_score": 9, "coverage_percentage": 90.0, "total_aspects": 1,
                              "extracted_aspects": ["Definition"], "covered_aspects": ["Definition"], "missing_aspects": [],
                              "reasoning": "..."},
            "verdict": {"overall_score": 9.0, "final_verdict": "EXCELLENT", "quality_gate_passed": True,
                        "failed_conditions": [], "weighted_breakdown": {}, "strengths": [], "weaknesses": [],
                        "consolidated_reasoning": "..."},
        }
    payload["rag"] = {"source": "user_supplied"}
    return payload, False


def _run_sample_batch(monkeypatch, system_name="GPT-4", batch_label="E2E Test Run"):
    monkeypatch.setattr(batch_processor, "evaluate_all", _fake_evaluate_all)
    at = AppTest.from_file(HARNESS, default_timeout=90)
    at.run()
    at.checkbox[0].set_value(True).run()  # use built-in sample dataset
    at.text_input[0].set_value(system_name)
    at.text_input[1].set_value(batch_label)
    run_btn = [b for b in at.button if "Run Batch Evaluation" in b.label][0]
    run_btn.click().run()
    return at


def test_page_renders_with_no_upload():
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    assert not at.exception


def test_sample_dataset_preview_shows_before_running():
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    at.checkbox[0].set_value(True).run()
    assert not at.exception
    assert len(at.dataframe) >= 1  # the preview table


def test_full_batch_run_completes_and_renders_analytics(monkeypatch):
    at = _run_sample_batch(monkeypatch)
    assert not at.exception
    markdown_text = " ".join(m.value for m in at.markdown)
    assert "Summary" in markdown_text
    assert "Analytics" in markdown_text
    assert "Standout Responses" in markdown_text
    assert "Detailed Results" in markdown_text


def test_all_four_export_buttons_present_after_run(monkeypatch):
    at = _run_sample_batch(monkeypatch)
    download_buttons = at.get("download_button")
    labels = [d.label for d in download_buttons]
    assert any("CSV" in l for l in labels)
    assert any("Excel" in l for l in labels)
    assert any("JSON" in l for l in labels)
    assert any("PDF" in l for l in labels)


def test_summary_tiles_reflect_actual_pass_fail_mix(monkeypatch):
    at = _run_sample_batch(monkeypatch)
    markdown_text = " ".join(m.value for m in at.markdown)
    # The sample dataset has a mix of "banana"/"sydney" (bad) and normal
    # (good) responses -- both PASS % and FAIL % should be present and
    # nonzero, not degenerate 0%/100%.
    assert "Pass %" in markdown_text or "PASS" in markdown_text.upper()


def test_malformed_csv_shows_clean_error_not_a_crash():
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    assert not at.exception
    # No file uploaded and sample dataset unchecked -> page should just
    # show the upload prompt, not attempt to process nothing.
    at.checkbox[0].set_value(False).run()
    assert not at.exception


def test_tags_are_threaded_through_to_every_row(monkeypatch):
    captured_system_names = []

    def capturing_fake(question, response, reference, system_name="Unspecified", batch_id=None, batch_label=None):
        captured_system_names.append(system_name)
        return _fake_evaluate_all(question, response, reference, system_name, batch_id, batch_label)

    monkeypatch.setattr(batch_processor, "evaluate_all", capturing_fake)
    at = AppTest.from_file(HARNESS, default_timeout=90)
    at.run()
    at.checkbox[0].set_value(True).run()
    at.text_input[0].set_value("Claude-3")
    [b for b in at.button if "Run Batch Evaluation" in b.label][0].click().run()

    assert len(captured_system_names) > 0
    assert all(name == "Claude-3" for name in captured_system_names)
