"""
Benchmark Validation / Batch Evaluation
-----------------------------------------
Upload a CSV of question/response/reference_answer triples, validate it,
run every row through the full multi-agent pipeline (/evaluate/all), and
review aggregate quality analytics -- with graceful handling of malformed
CSVs, missing values, and per-row API failures.

render() keeps its original signature so app.py's nav wiring is untouched.
"""

import pandas as pd
import streamlit as st

from components.badges import card, section_label, metric_tile
from components.charts import render_distribution_chart, render_score_bar, render_radar_chart
from components.batch_charts import render_pass_fail_pie, render_score_trend
from components.batch_summary import summary_tiles, standout_responses

from utils.csv_parser import load_and_validate_csv, sample_dataset, REQUIRED_COLUMNS
from utils.batch_processor import run_batch
from utils.download_utils import to_csv_bytes, to_excel_bytes, to_json_bytes
from utils.pdf_export import build_batch_evaluation_pdf


def render():
    st.markdown("<div class='hero-title' style='font-size:30px'>Benchmark Validation</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hero-sub'>Upload a CSV of question / response / reference-answer triples to run "
        "batch evaluation across the full multi-agent pipeline and review aggregate quality metrics.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    df = _upload_and_validate_step()
    if df is None:
        return

    _preview_step(df)

    st.write("")
    section_label("3. Tag This Run (for the Dashboard)")
    with card():
        t1, t2 = st.columns(2)
        with t1:
            system_name = st.text_input(
                "🏷️ AI System / Model Name (optional)",
                placeholder="e.g. GPT-4, Claude-3-Sonnet...",
                help="Groups this batch under a system name so it can be compared "
                     "against other systems on the Dashboard.",
                key="batch_system_name",
            )
        with t2:
            batch_label = st.text_input(
                "📝 Run Label (optional)",
                placeholder="e.g. \"Trivia set v2\", \"Post-finetune check\"...",
                help="A human-readable name for this specific batch run, shown in the "
                     "Dashboard's batch history table.",
                key="batch_run_label",
            )

    st.write("")
    run_col, count_col = st.columns([1, 3])
    with run_col:
        run = st.button(f"▶ Run Batch Evaluation ({len(df)} rows)", use_container_width=True)
    with count_col:
        st.caption(
            "Each row calls `/evaluate/all` sequentially. Estimated time depends on backend latency; "
            "progress and ETA are shown live below once you start. Every row is automatically "
            "recorded to evaluation history for the Dashboard."
        )

    if run:
        st.session_state.pop("batch_results", None)
        _run_batch_step(
            df,
            system_name=(system_name or "").strip() or "Unspecified",
            batch_label=(batch_label or "").strip() or None,
        )

    if "batch_results" in st.session_state:
        _render_results(st.session_state["batch_results"], st.session_state.get("batch_tags", {}))


# --------------------------------------------------------------------------
# STEP 1 -- Upload & Validate
# --------------------------------------------------------------------------

def _upload_and_validate_step():
    section_label("1. Upload Dataset")
    with card():
        st.caption("Expected columns: `question`, `response`, `reference_answer` (optional)")
        uploaded = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
        use_sample = st.checkbox("No file? Use a small built-in sample dataset instead", value=uploaded is None)

    df, errors, warnings = None, [], []

    if uploaded is not None:
        df, errors, warnings = load_and_validate_csv(uploaded)
    elif use_sample:
        df = sample_dataset()

    if df is None and not errors and not use_sample:
        return None  # nothing uploaded yet, nothing to show

    if errors:
        with card():
            st.error(
                "This CSV can't be evaluated yet:\n\n" + "\n".join(f"- {e}" for e in errors)
            )
            st.caption(f"Required columns: {', '.join(REQUIRED_COLUMNS)}")
        return None

    if warnings:
        with card():
            for w in warnings:
                st.warning(w, icon="⚠️")

    return df


# --------------------------------------------------------------------------
# STEP 2 -- Preview
# --------------------------------------------------------------------------

def _preview_step(df: pd.DataFrame):
    st.write("")
    section_label("2. Dataset Preview")
    with card():
        m1, m2, m3 = st.columns(3)
        with m1:
            metric_tile("Rows", str(len(df)))
        with m2:
            metric_tile("Columns", str(len(df.columns)))
        with m3:
            missing = int(df.isna().sum().sum()) + int((df.astype(str) == "").sum().sum())
            metric_tile("Missing Values", str(missing))
        st.write("")
        st.dataframe(df.head(10), use_container_width=True)


# --------------------------------------------------------------------------
# STEP 3 -- Run
# --------------------------------------------------------------------------

def _run_batch_step(df: pd.DataFrame, system_name: str = "Unspecified", batch_label: str | None = None):
    section_label("4. Running Batch Evaluation")
    with card():
        progress_bar = st.progress(0.0, text="Starting batch evaluation...")
        status_line = st.empty()

        def _on_progress(done, total, elapsed, remaining):
            pct = done / total
            status_line.caption(
                f"Row {done}/{total}  •  Elapsed: {elapsed:.1f}s  •  Estimated remaining: {remaining:.1f}s"
            )
            progress_bar.progress(pct, text=f"Evaluating row {done}/{total}...")

        results = run_batch(
            df,
            progress_callback=_on_progress,
            system_name=system_name,
            batch_label=batch_label,
        )
        progress_bar.progress(1.0, text=f"Done — {len(df)} rows evaluated in {results['total_time']:.1f}s.")

    st.session_state["batch_results"] = results
    st.session_state["batch_tags"] = {"system_name": system_name, "batch_label": batch_label or ""}


# --------------------------------------------------------------------------
# STEP 4 -- Results, Analytics, Export
# --------------------------------------------------------------------------

def _render_results(results: dict, tags: dict = None):
    tags = tags or {}
    table: pd.DataFrame = results["table"]
    errors: list = results["errors"]

    if results.get("used_mock"):
        st.info(
            "⚠️ Backend not reachable for at least one row — some results below use demo data "
            "so the dashboard layout can still be reviewed. Connect the FastAPI backend for real scores.",
            icon="⚠️",
        )

    st.write("")
    section_label("5. Summary")
    summary_tiles(table)

    # ---------------- Failed rows ----------------
    if errors:
        st.write("")
        with card():
            section_label(f"⚠ {len(errors)} Row(s) Failed")
            st.caption("These rows raised an error during evaluation and were skipped; the rest of the batch continued.")
            st.dataframe(pd.DataFrame(errors), use_container_width=True)

    # ---------------- Charts ----------------
    scored = table[table["final_verdict"] != "ERROR"]

    st.write("")
    section_label("6. Analytics")

    c1, c2 = st.columns(2)
    with c1:
        with card():
            st.markdown("**Score Distribution (Overall)**")
            render_distribution_chart(scored["overall_score"].dropna().tolist(), key="dist_batch")
    with c2:
        with card():
            st.markdown("**Pass / Fail Breakdown**")
            n_pass = int((scored["pass_fail"] == "PASS").sum())
            n_fail = int((scored["pass_fail"] == "FAIL").sum())
            render_pass_fail_pie(n_pass, n_fail, len(errors), key="pie_batch")

    avg_scores = {
        "Relevance": scored["relevance"].mean(),
        "Accuracy": scored["accuracy"].mean(),
        "Hallucination": scored["hallucination"].mean(),
        "Completeness": scored["completeness"].mean(),
    }
    c3, c4 = st.columns(2)
    with c3:
        with card():
            st.markdown("**Agent-wise Average (Radar)**")
            render_radar_chart(avg_scores, key="radar_batch")
    with c4:
        with card():
            st.markdown("**Agent-wise Average (Bar)**")
            render_score_bar(avg_scores, key="bar_batch")

    with card():
        st.markdown("**Overall Score Trend (Upload Order)**")
        render_score_trend(scored["overall_score"].dropna().tolist(), key="trend_batch")

    # ---------------- Standout responses ----------------
    st.write("")
    section_label("7. Standout Responses")
    standout_responses(table)

    # ---------------- Detailed table ----------------
    st.write("")
    section_label("8. Detailed Results")
    with card():
        display_cols = [
            "#", "question", "overall_score", "relevance", "accuracy",
            "hallucination", "completeness", "final_verdict", "pass_fail",
        ]
        st.dataframe(table[display_cols], use_container_width=True)

        st.write("")
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.download_button(
                "⬇ Download CSV",
                data=to_csv_bytes(table),
                file_name="batch_evaluation_report.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with d2:
            try:
                excel_bytes = to_excel_bytes(table)
                st.download_button(
                    "⬇ Download Excel",
                    data=excel_bytes,
                    file_name="batch_evaluation_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            except ImportError:
                st.caption("Install `openpyxl` to enable Excel export.")
        with d3:
            st.download_button(
                "⬇ Download JSON (full detail)",
                data=to_json_bytes(results["full_rows"]),
                file_name="batch_evaluation_full.json",
                mime="application/json",
                use_container_width=True,
            )
        with d4:
            pdf_bytes = build_batch_evaluation_pdf(
                table,
                system_name=tags.get("system_name", "Unspecified"),
                batch_label=tags.get("batch_label", ""),
            )
            st.download_button(
                "📄 Download PDF Report",
                data=pdf_bytes,
                file_name="batch_evaluation_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
