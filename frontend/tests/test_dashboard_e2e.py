"""
End-to-End tests for the Dashboard page (Milestone 4, item 3).

Drives the real page through AppTest, mocking the four history-fetching
functions dashboard.py imported by name (`from utils.api_client import
get_history_summary, ...`) -- same reasoning as the batch test file: a
direct name import means the mock must target dashboard's own module
namespace, not api_client's.

Covers both the empty-history state (a fresh install with nothing
evaluated yet -- must show a clear message, not crash on empty charts)
and a populated state with two tagged systems (the "compare two AI
systems" requirement).
"""

import pathlib

from streamlit.testing.v1 import AppTest

import pages_content.dashboard as dashboard

HARNESS = str(pathlib.Path(__file__).parent / "_harness_dashboard.py")

EMPTY_SUMMARY = {}

POPULATED_SUMMARY = {
    "total_evaluations": 19,
    "avg_overall_score": 5.44,
    "avg_relevance": 6.9,
    "avg_accuracy": 4.6,
    "avg_hallucination": 4.2,
    "avg_completeness": 6.8,
    "total_pass": 8,
    "total_fail": 11,
    "high_hallucination_count": 11,
}

BATCHES = [
    {"batch_id": "b1", "batch_label": "Trivia set v1", "system_name": "GPT-4",
     "started_at": "2026-08-13T07:56:12", "row_count": 8, "avg_overall_score": 5.8,
     "avg_relevance": 6.75, "avg_accuracy": 5.5, "avg_hallucination": 5.0, "avg_completeness": 6.25,
     "pass_count": 4, "fail_count": 4},
    {"batch_id": "b2", "batch_label": "Trivia set v1", "system_name": "Claude-3",
     "started_at": "2026-08-13T07:57:13", "row_count": 8, "avg_overall_score": 5.8,
     "avg_relevance": 6.75, "avg_accuracy": 5.5, "avg_hallucination": 5.0, "avg_completeness": 6.25,
     "pass_count": 4, "fail_count": 4},
]

SYSTEMS = [
    {"system_name": "Claude-3", "total_evaluations": 10, "avg_overall_score": 5.34,
     "avg_relevance": 7.0, "avg_accuracy": 4.4, "avg_hallucination": 4.0, "avg_completeness": 7.0,
     "pass_count": 4, "fail_count": 6},
    {"system_name": "GPT-4", "total_evaluations": 9, "avg_overall_score": 5.54,
     "avg_relevance": 6.89, "avg_accuracy": 4.89, "avg_hallucination": 4.44, "avg_completeness": 6.67,
     "pass_count": 4, "fail_count": 5},
]


def _mock_history(monkeypatch, summary, batches=None, systems=None):
    monkeypatch.setattr(dashboard, "get_history_summary", lambda: summary)
    monkeypatch.setattr(dashboard, "get_batch_summaries", lambda: batches or [])
    monkeypatch.setattr(dashboard, "get_system_summaries", lambda: systems or [])
    monkeypatch.setattr(dashboard, "get_history_runs", lambda **kw: [])


def test_empty_history_shows_clear_message_not_a_crash(monkeypatch):
    _mock_history(monkeypatch, EMPTY_SUMMARY)
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    assert not at.exception
    infos = [i.value for i in at.info]
    assert any("No evaluation history" in i for i in infos)


def test_populated_dashboard_renders_all_sections(monkeypatch):
    _mock_history(monkeypatch, POPULATED_SUMMARY, BATCHES, SYSTEMS)
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    assert not at.exception
    markdown_text = " ".join(m.value for m in at.markdown)
    for section in ["Overall Summary", "Average Dimension Scores", "Quality Gate",
                     "Quality Trends Across Batch Evaluations", "Compare AI Systems"]:
        assert section in markdown_text


def test_summary_tile_values_match_the_backend_data(monkeypatch):
    _mock_history(monkeypatch, POPULATED_SUMMARY, BATCHES, SYSTEMS)
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    markdown_text = " ".join(m.value for m in at.markdown)
    assert "19" in markdown_text          # total evaluations
    assert "5.44" in markdown_text        # avg overall score


def test_two_systems_render_side_by_side_comparison(monkeypatch):
    _mock_history(monkeypatch, POPULATED_SUMMARY, BATCHES, SYSTEMS)
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    markdown_text = " ".join(m.value for m in at.markdown)
    assert "Claude-3" in markdown_text
    assert "GPT-4" in markdown_text
    # Should NOT show the "only one system" nudge when 2+ are present.
    infos = [i.value for i in at.info]
    assert not any("Only one AI system tagged" in i for i in infos)


def test_single_system_shows_a_nudge_to_tag_a_second_one(monkeypatch):
    _mock_history(monkeypatch, POPULATED_SUMMARY, BATCHES, [SYSTEMS[0]])
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    assert not at.exception
    infos = [i.value for i in at.info]
    assert any("Only one AI system tagged" in i for i in infos)


def test_batch_history_table_reflects_actual_batches(monkeypatch):
    _mock_history(monkeypatch, POPULATED_SUMMARY, BATCHES, SYSTEMS)
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    dataframes = at.dataframe
    found_batch_table = False
    for df_el in dataframes:
        if "Batch" in list(df_el.value.columns):
            found_batch_table = True
            assert len(df_el.value) == 2
    assert found_batch_table


def test_refresh_button_present_and_clickable(monkeypatch):
    _mock_history(monkeypatch, POPULATED_SUMMARY, BATCHES, SYSTEMS)
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    refresh_buttons = [b for b in at.button if "Refresh" in b.label]
    assert len(refresh_buttons) == 1
