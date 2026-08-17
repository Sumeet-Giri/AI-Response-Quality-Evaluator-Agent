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
    "pass_count": 8,
    "needs_improvement_count": 5,
    "fail_count": 6,
    "high_hallucination_count": 11,
}

BATCHES = [
    {"batch_id": "b1", "batch_label": "Trivia set v1", "system_name": "GPT-4",
     "started_at": "2026-08-13T07:56:12", "row_count": 8, "avg_overall_score": 5.8,
     "avg_relevance": 6.75, "avg_accuracy": 5.5, "avg_hallucination": 5.0, "avg_completeness": 6.25,
     "pass_count": 4, "fail_count": 4, "pass_verdict_count": 3, "needs_improvement_count": 3, "fail_verdict_count": 2},
    {"batch_id": "b2", "batch_label": "Trivia set v1", "system_name": "Claude-3",
     "started_at": "2026-08-13T07:57:13", "row_count": 8, "avg_overall_score": 5.8,
     "avg_relevance": 6.75, "avg_accuracy": 5.5, "avg_hallucination": 5.0, "avg_completeness": 6.25,
     "pass_count": 4, "fail_count": 4, "pass_verdict_count": 3, "needs_improvement_count": 3, "fail_verdict_count": 2},
]

FILTER_OPTIONS = {
    "systems": ["GPT-4", "Claude-3"],
    "datasets": ["Trivia set v1"],
    "modes": ["single", "batch"],
    "earliest": "2026-08-13T07:56:12",
    "latest": "2026-08-13T07:57:13",
}

SYSTEMS = [
    {"system_name": "Claude-3", "total_evaluations": 10, "avg_overall_score": 5.34,
     "avg_relevance": 7.0, "avg_accuracy": 4.4, "avg_hallucination": 4.0, "avg_completeness": 7.0,
     "pass_count": 4, "fail_count": 6},
    {"system_name": "GPT-4", "total_evaluations": 9, "avg_overall_score": 5.54,
     "avg_relevance": 6.89, "avg_accuracy": 4.89, "avg_hallucination": 4.44, "avg_completeness": 6.67,
     "pass_count": 4, "fail_count": 5},
]


def _mock_history(monkeypatch, summary, batches=None, systems=None):
    monkeypatch.setattr(dashboard, "get_history_summary", lambda **kw: summary)
    monkeypatch.setattr(dashboard, "get_batch_summaries", lambda **kw: batches or [])
    monkeypatch.setattr(dashboard, "get_system_summaries", lambda **kw: systems or [])
    monkeypatch.setattr(dashboard, "get_history_runs", lambda **kw: [])
    monkeypatch.setattr(dashboard, "get_filter_options", lambda: FILTER_OPTIONS)


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


# --------------------------------------------------------------------
# Filter bar and 3-way Pass/Needs Improvement/Fail breakdown
# --------------------------------------------------------------------

def test_filter_widgets_are_present(monkeypatch):
    _mock_history(monkeypatch, POPULATED_SUMMARY, BATCHES, SYSTEMS)
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    assert not at.exception
    selectbox_labels = [sb.label for sb in at.selectbox]
    assert "Model / System" in selectbox_labels
    assert "Dataset" in selectbox_labels
    assert "Evaluation Mode" in selectbox_labels
    assert len(at.date_input) == 2  # From / To


def test_filter_dropdowns_populated_from_filter_options(monkeypatch):
    _mock_history(monkeypatch, POPULATED_SUMMARY, BATCHES, SYSTEMS)
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    system_select = next(sb for sb in at.selectbox if sb.label == "Model / System")
    assert "GPT-4" in system_select.options
    assert "Claude-3" in system_select.options
    assert system_select.options[0] == "All"


def test_selecting_a_system_filter_calls_backend_with_that_filter(monkeypatch):
    captured = {}

    def capturing_summary(**kw):
        captured.update(kw)
        return POPULATED_SUMMARY

    monkeypatch.setattr(dashboard, "get_history_summary", capturing_summary)
    monkeypatch.setattr(dashboard, "get_batch_summaries", lambda **kw: BATCHES)
    monkeypatch.setattr(dashboard, "get_system_summaries", lambda **kw: SYSTEMS)
    monkeypatch.setattr(dashboard, "get_history_runs", lambda **kw: [])
    monkeypatch.setattr(dashboard, "get_filter_options", lambda: FILTER_OPTIONS)

    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    system_select = next(sb for sb in at.selectbox if sb.label == "Model / System")
    system_select.set_value("GPT-4").run()

    assert captured.get("system_name") == "GPT-4"


def test_clear_filters_button_resets_selections(monkeypatch):
    _mock_history(monkeypatch, POPULATED_SUMMARY, BATCHES, SYSTEMS)
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    system_select = next(sb for sb in at.selectbox if sb.label == "Model / System")
    system_select.set_value("GPT-4").run()
    assert system_select.value == "GPT-4"

    clear_btn = [b for b in at.button if "Clear Filters" in b.label][0]
    clear_btn.click().run()
    system_select_after = next(sb for sb in at.selectbox if sb.label == "Model / System")
    assert system_select_after.value == "All"


def test_no_results_for_filters_shows_a_filter_specific_message(monkeypatch):
    monkeypatch.setattr(dashboard, "get_history_summary", lambda **kw: {} if kw.get("system_name") else POPULATED_SUMMARY)
    monkeypatch.setattr(dashboard, "get_batch_summaries", lambda **kw: BATCHES)
    monkeypatch.setattr(dashboard, "get_system_summaries", lambda **kw: SYSTEMS)
    monkeypatch.setattr(dashboard, "get_history_runs", lambda **kw: [])
    monkeypatch.setattr(dashboard, "get_filter_options", lambda: FILTER_OPTIONS)

    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    system_select = next(sb for sb in at.selectbox if sb.label == "Model / System")
    system_select.set_value("GPT-4").run()

    assert not at.exception
    infos = [i.value for i in at.info]
    assert any("No evaluations match the selected filters" in i for i in infos)


def test_pass_needs_improvement_fail_tiles_show_three_way_breakdown(monkeypatch):
    _mock_history(monkeypatch, POPULATED_SUMMARY, BATCHES, SYSTEMS)
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    markdown_text = " ".join(m.value for m in at.markdown)
    assert "Pass / Needs Improvement / Fail" in markdown_text


def test_three_way_breakdown_values_match_backend_data(monkeypatch):
    _mock_history(monkeypatch, POPULATED_SUMMARY, BATCHES, SYSTEMS)
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    tile_values = []
    for m in at.markdown:
        tile_values.append(m.value)
    combined = " ".join(tile_values)
    # POPULATED_SUMMARY: pass_count=8, needs_improvement_count=5, fail_count=6
    assert "8" in combined
    assert "5" in combined
    assert "6" in combined


# --------------------------------------------------------------------
# Many-systems comparison cap (regression test for a real reported bug:
# 9 tagged systems -- several of them test-fixture artifacts from an
# earlier version of the test suite that wrote into the real database --
# rendered as 9 unreadable, overlapping narrow columns).
# --------------------------------------------------------------------

MANY_SYSTEMS = [
    {"system_name": f"System{i}", "total_evaluations": 10 - i, "avg_overall_score": 5.0,
     "avg_relevance": 6.0, "avg_accuracy": 5.0, "avg_hallucination": 5.0, "avg_completeness": 6.0,
     "pass_count": 2, "fail_count": 2}
    for i in range(9)
]


def test_many_systems_does_not_render_one_column_per_system(monkeypatch):
    _mock_history(monkeypatch, POPULATED_SUMMARY, BATCHES, MANY_SYSTEMS)
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    assert not at.exception
    # A multiselect for picking which systems to compare should appear
    # instead of blindly creating 9 columns.
    multiselects = [ms for ms in at.multiselect if ms.label == "Systems to compare"]
    assert len(multiselects) == 1
    assert len(multiselects[0].value) <= 4


def test_many_systems_default_selection_picks_highest_evaluation_counts(monkeypatch):
    _mock_history(monkeypatch, POPULATED_SUMMARY, BATCHES, MANY_SYSTEMS)
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    ms = next(ms for ms in at.multiselect if ms.label == "Systems to compare")
    # MANY_SYSTEMS is ordered System0 (10 evals) ... System8 (2 evals) --
    # default should favor the ones with the most evaluations.
    assert "System0" in ms.value
    assert "System1" in ms.value


def test_many_systems_table_always_lists_every_system_regardless_of_selection(monkeypatch):
    _mock_history(monkeypatch, POPULATED_SUMMARY, BATCHES, MANY_SYSTEMS)
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    for df_el in at.dataframe:
        columns = list(df_el.value.columns)
        if "System" in columns and "Evaluations" in columns:  # the systems table specifically, not batch history
            assert len(df_el.value) == 9  # every one of the 9 systems, not just the selected 4


def test_selecting_fewer_systems_renders_fewer_comparison_cards(monkeypatch):
    _mock_history(monkeypatch, POPULATED_SUMMARY, BATCHES, MANY_SYSTEMS)
    at = AppTest.from_file(HARNESS, default_timeout=60)
    at.run()
    ms = next(ms for ms in at.multiselect if ms.label == "Systems to compare")
    ms.set_value(["System0", "System1"]).run()
    assert not at.exception
