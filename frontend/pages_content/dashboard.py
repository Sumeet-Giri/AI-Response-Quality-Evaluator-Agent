"""
Dashboard (Milestone 4)
-------------------------
Aggregate view across ALL evaluation history -- single evaluations and
every batch run -- pulled from the backend's SQLite-backed /history/*
endpoints. This is what makes "quality trends across batch evaluations"
and "compare two AI systems" real: both require data that outlives one
Streamlit session, which is exactly what the history store provides.

Filters (date range, model/system, dataset, evaluation mode) apply to
every section on the page -- summary tiles, dimension scores, the
Pass/Needs Improvement/Fail breakdown, batch trends, and system
comparison all read from the same filtered query, not just the top
tiles, so the whole page consistently reflects the selected filters.

Deliberately reuses existing chart components (render_radar_chart,
render_score_bar, render_score_trend, render_pass_fail_pie,
render_verdict_breakdown_pie) rather than introducing new near-duplicate
chart code -- the only genuinely new visual here is laying those same
components out per-system for comparison.
"""

import pandas as pd
import streamlit as st

from components.badges import card, section_label, metric_tile
from components.charts import render_radar_chart, render_score_bar, render_distribution_chart
from components.batch_charts import render_pass_fail_pie, render_verdict_breakdown_pie, render_score_trend

from utils.api_client import (
    get_history_summary,
    get_batch_summaries,
    get_system_summaries,
    get_history_runs,
    get_filter_options,
)


def render():
    st.markdown("<div class='hero-title' style='font-size:30px'>Dashboard</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hero-sub'>Aggregate quality metrics across every evaluation ever run through this "
        "platform -- single evaluations and batch runs alike -- persisted in the backend so this reflects "
        "real history, not just the current session.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    filters = _render_filter_bar()

    r1, r2 = st.columns([1, 5])
    with r1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    summary = get_history_summary(**filters)
    total = summary.get("total_evaluations") or 0

    if not total:
        with card():
            if any(filters.values()):
                st.info(
                    "No evaluations match the selected filters. Try widening the date range or "
                    "clearing a filter above.",
                    icon="🔍",
                )
            else:
                st.info(
                    "No evaluation history yet. Run a Single Evaluation or a Batch Evaluation first -- "
                    "every evaluation is automatically recorded here.",
                    icon="📭",
                )
        return

    # ---------------- Overall summary ----------------
    st.write("")
    section_label("Overall Summary")
    _render_summary_tiles(summary)

    # ---------------- Average dimension scores ----------------
    st.write("")
    section_label("Average Dimension Scores")
    avg_scores = {
        "Relevance": summary.get("avg_relevance") or 0,
        "Accuracy": summary.get("avg_accuracy") or 0,
        "Hallucination": summary.get("avg_hallucination") or 0,
        "Completeness": summary.get("avg_completeness") or 0,
    }
    c1, c2 = st.columns(2)
    with c1:
        with card():
            st.markdown("**Radar**")
            render_radar_chart(avg_scores, key="dash_radar_overall")
    with c2:
        with card():
            st.markdown("**Bar**")
            render_score_bar(avg_scores, key="dash_bar_overall")

    # ---------------- Verdict breakdown + hallucination frequency ----------------
    st.write("")
    section_label("Quality Verdict Breakdown & Hallucination Frequency")
    c3, c4 = st.columns(2)
    with c3:
        with card():
            st.markdown("**Pass / Needs Improvement / Fail**")
            render_verdict_breakdown_pie(
                pass_count=summary.get("pass_count") or 0,
                needs_improvement_count=summary.get("needs_improvement_count") or 0,
                fail_count=summary.get("fail_count") or 0,
                key="dash_verdict_pie",
            )
            st.caption(
                "Pass = EXCELLENT/GOOD · Needs Improvement = NEEDS IMPROVEMENT/POOR · "
                "Fail = quality gate failed."
            )
    with c4:
        with card():
            st.markdown("**Hallucination Risk**")
            high_halluc = summary.get("high_hallucination_count") or 0
            metric_tile("Responses w/ High Hallucination Risk", str(high_halluc))
            st.caption(
                f"{high_halluc} of {total} recorded evaluations scored below 4/10 on the "
                f"Hallucination-Free scale (i.e. hallucination_score < 4)."
            )
            metric_tile("Avg Hallucination-Free Score", f"{(summary.get('avg_hallucination') or 0):.1f}/10")

    with card():
        st.markdown("**Quality Gate (Binary) — Pass / Fail**")
        render_pass_fail_pie(
            pass_count=summary.get("total_pass") or 0,
            fail_count=summary.get("total_fail") or 0,
            error_count=0,
            key="dash_pass_fail_pie",
        )

    # ---------------- Trends across batch evaluations ----------------
    st.write("")
    section_label("Quality Trends Across Batch Evaluations")
    batch_filters = {k: v for k, v in filters.items() if k != "mode"}  # get_batches has no mode param
    batches = get_batch_summaries(**batch_filters)
    if not batches:
        with card():
            st.caption("No batch runs match the current filters -- run a Benchmark Validation batch, "
                       "or widen the filters above, to populate this section.")
    else:
        batches_sorted = sorted(batches, key=lambda b: b["started_at"])
        with card():
            st.markdown("**Average Overall Score per Batch Run (oldest → newest)**")
            render_score_trend(
                [b["avg_overall_score"] or 0 for b in batches_sorted],
                key="dash_batch_trend",
                x_axis_label="Batch #",
            )

        with card():
            st.markdown("**Batch Run History**")
            df = pd.DataFrame([
                {
                    "Batch": b.get("batch_label") or b["batch_id"],
                    "System": b["system_name"],
                    "Started": b["started_at"][:19].replace("T", " "),
                    "Rows": b["row_count"],
                    "Avg Score": round(b["avg_overall_score"] or 0, 2),
                    "Pass": b.get("pass_verdict_count", b["pass_count"]),
                    "Needs Improvement": b.get("needs_improvement_count", 0),
                    "Fail": b.get("fail_verdict_count", b["fail_count"]),
                }
                for b in batches_sorted[::-1]
            ])
            st.dataframe(df, use_container_width=True)

    # ---------------- System comparison ----------------
    st.write("")
    section_label("Compare AI Systems")
    system_filters = {k: v for k, v in filters.items() if k != "system_name"}  # comparison can't filter on itself
    systems = get_system_summaries(**system_filters)
    _render_system_comparison(systems)


def _render_filter_bar():
    """
    Renders the filter row and returns a dict of the currently selected
    filters (system_name, mode, dataset, date_from, date_to), each None
    if not set -- ready to pass straight through as kwargs to the
    get_history_* API functions, which already treat None as "no filter".
    """
    options = get_filter_options()

    with card():
        st.markdown("**Filters**")
        f1, f2, f3, f4, f5 = st.columns([1.3, 1.3, 1, 1, 1])

        with f1:
            system_choice = st.selectbox(
                "Model / System",
                ["All"] + options.get("systems", []),
                key="dash_filter_system",
            )
        with f2:
            dataset_choice = st.selectbox(
                "Dataset",
                ["All"] + options.get("datasets", []),
                key="dash_filter_dataset",
                help="Filters by the Run Label tagged on a batch (or dataset name, if you use that "
                     "field for it). Single evaluations have no dataset and are excluded when this filter is set.",
            )
        with f3:
            mode_choice = st.selectbox(
                "Evaluation Mode",
                ["All", "single", "batch"],
                key="dash_filter_mode",
            )
        with f4:
            date_from = st.date_input("From", value=None, key="dash_filter_date_from")
        with f5:
            date_to = st.date_input("To", value=None, key="dash_filter_date_to")

        if st.button("✕ Clear Filters", key="dash_clear_filters"):
            for k in ["dash_filter_system", "dash_filter_dataset", "dash_filter_mode",
                      "dash_filter_date_from", "dash_filter_date_to"]:
                st.session_state.pop(k, None)
            st.rerun()

    return {
        "system_name": None if system_choice == "All" else system_choice,
        "dataset": None if dataset_choice == "All" else dataset_choice,
        "mode": None if mode_choice == "All" else mode_choice,
        "date_from": date_from if date_from else None,
        "date_to": date_to if date_to else None,
    }


def _render_summary_tiles(summary: dict):
    total = summary.get("total_evaluations") or 0
    total_pass = summary.get("total_pass") or 0
    total_fail = summary.get("total_fail") or 0
    denom = max(1, total_pass + total_fail)

    r1 = st.columns(4)
    with r1[0]:
        metric_tile("Total Evaluations", str(total))
    with r1[1]:
        metric_tile("Average Overall Score", f"{(summary.get('avg_overall_score') or 0):.2f}/10")
    with r1[2]:
        metric_tile("Pass %", f"{total_pass / denom * 100:.0f}%")
    with r1[3]:
        metric_tile("Fail %", f"{total_fail / denom * 100:.0f}%")

    r2 = st.columns(4)
    with r2[0]:
        metric_tile("Pass (Verdict)", str(summary.get("pass_count") or 0))
    with r2[1]:
        metric_tile("Needs Improvement", str(summary.get("needs_improvement_count") or 0))
    with r2[2]:
        metric_tile("Fail (Verdict)", str(summary.get("fail_count") or 0))
    with r2[3]:
        metric_tile("Avg Completeness", f"{(summary.get('avg_completeness') or 0):.1f}/10")


def _render_system_comparison(systems: list[dict]):
    if not systems:
        with card():
            st.caption("No evaluations recorded yet.")
        return

    if len(systems) == 1:
        with card():
            st.info(
                f"Only one AI system tagged so far (**{systems[0]['system_name']}**). "
                "Tag evaluations with a different System Name on the Single Evaluation or "
                "Benchmark Validation pages to unlock a side-by-side comparison here -- this is "
                "how the platform demonstrates evaluating two distinct AI systems.",
                icon="🔀",
            )
        # Still show the one system's profile so the section isn't empty.
        with card():
            st.markdown(f"**{systems[0]['system_name']}**")
            _system_mini_summary(systems[0])
        return

    MAX_COMPARE_COLUMNS = 4
    display_systems = systems

    if len(systems) > MAX_COMPARE_COLUMNS:
        # Squeezing one narrow column per system stops being readable well
        # before this point -- labels wrap, bars overlap, text truncates.
        # Let the user pick which ones to actually compare side-by-side
        # instead; the full table below always lists every system anyway.
        with card():
            st.caption(
                f"{len(systems)} systems are tagged in the current filter -- showing all of them as "
                f"side-by-side cards stops being readable, so pick up to {MAX_COMPARE_COLUMNS} below. "
                "Every system is always listed in the table beneath the cards."
            )
            system_names = [s["system_name"] for s in systems]
            default_names = [
                s["system_name"]
                for s in sorted(systems, key=lambda s: s["total_evaluations"], reverse=True)[:MAX_COMPARE_COLUMNS]
            ]
            selected_names = st.multiselect(
                "Systems to compare",
                options=system_names,
                default=default_names,
                max_selections=MAX_COMPARE_COLUMNS,
                key="dash_compare_system_select",
            )
        selected_set = set(selected_names)
        display_systems = [s for s in systems if s["system_name"] in selected_set]
        if not display_systems:
            display_systems = sorted(systems, key=lambda s: s["total_evaluations"], reverse=True)[:MAX_COMPARE_COLUMNS]

    cols = st.columns(len(display_systems))
    for col, sysrow in zip(cols, display_systems):
        with col:
            with card():
                st.markdown(f"**{sysrow['system_name']}**")
                _system_mini_summary(sysrow)
                scores = {
                    "Relevance": sysrow.get("avg_relevance") or 0,
                    "Accuracy": sysrow.get("avg_accuracy") or 0,
                    "Hallucination": sysrow.get("avg_hallucination") or 0,
                    "Completeness": sysrow.get("avg_completeness") or 0,
                }
                render_score_bar(scores, key=f"dash_system_bar_{sysrow['system_name']}")

    with card():
        st.markdown("**All Systems, Side by Side**")
        df = pd.DataFrame([
            {
                "System": s["system_name"],
                "Evaluations": s["total_evaluations"],
                "Avg Overall": round(s["avg_overall_score"] or 0, 2),
                "Avg Relevance": round(s.get("avg_relevance") or 0, 2),
                "Avg Accuracy": round(s.get("avg_accuracy") or 0, 2),
                "Avg Hallucination": round(s.get("avg_hallucination") or 0, 2),
                "Avg Completeness": round(s.get("avg_completeness") or 0, 2),
                "Pass": s["pass_count"],
                "Fail": s["fail_count"],
            }
            for s in systems
        ])
        st.dataframe(df, use_container_width=True)


def _system_mini_summary(sysrow: dict):
    total = sysrow.get("total_evaluations") or 0
    pass_count = sysrow.get("pass_count") or 0
    denom = max(1, total)
    st.caption(
        f"{total} evaluation(s) · Avg Overall {round(sysrow.get('avg_overall_score') or 0, 2)}/10 · "
        f"Pass rate {pass_count / denom * 100:.0f}%"
    )
