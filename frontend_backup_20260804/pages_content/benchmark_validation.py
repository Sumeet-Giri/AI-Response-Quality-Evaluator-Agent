import io
import time
import pandas as pd
import streamlit as st

from components.badges import card_open, card_close, section_label, metric_tile
from components.charts import render_distribution_chart, render_score_bar
from utils.api_client import evaluate_all


def render():
    st.markdown("<div class='hero-title' style='font-size:30px'>Benchmark Validation</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hero-sub'>Upload a CSV of question / response / reference triples to run "
        "batch evaluation across the full agent pipeline and review aggregate quality metrics.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    section_label("1. Upload Benchmark Dataset")
    card_open()
    st.caption("Expected columns: `question`, `response`, `reference_answer` (optional)")
    uploaded = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")

    use_sample = st.checkbox("No file? Use a small built-in sample dataset instead", value=uploaded is None)
    card_close()

    df = None
    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
        except Exception as e:
            st.error(f"Could not read CSV: {e}")
    elif use_sample:
        df = _sample_dataset()

    if df is None:
        return

    st.write("")
    section_label("2. Preview")
    card_open()
    st.dataframe(df.head(10), use_container_width=True)
    card_close()

    st.write("")
    run = st.button(f"▶ Run Batch Evaluation ({len(df)} rows)")

    if run:
        results = _run_batch(df)
        st.session_state["benchmark_results"] = results

    if "benchmark_results" in st.session_state:
        _render_benchmark_results(st.session_state["benchmark_results"])


def _sample_dataset() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"question": "What causes rainbows?", "response": "Rainbows form when sunlight is refracted and reflected inside water droplets.", "reference_answer": "Refraction and reflection of light in water droplets."},
            {"question": "Who wrote Hamlet?", "response": "Hamlet was written by William Shakespeare in the early 1600s.", "reference_answer": "William Shakespeare."},
            {"question": "What is the capital of Australia?", "response": "The capital of Australia is Sydney.", "reference_answer": "Canberra."},
            {"question": "How does photosynthesis work?", "response": "Plants use sunlight, water, and CO2 to produce glucose and oxygen via chlorophyll.", "reference_answer": "Conversion of light energy into chemical energy using chlorophyll."},
            {"question": "What is the speed of light?", "response": "The speed of light in vacuum is approximately 300,000 km/s.", "reference_answer": "299,792 km/s in a vacuum."},
        ]
    )


def _run_batch(df: pd.DataFrame):
    progress = st.progress(0.0, text="Starting batch evaluation...")
    rows = []
    n = len(df)
    for i, row in df.iterrows():
        q = str(row.get("question", ""))
        r = str(row.get("response", ""))
        ref = str(row.get("reference_answer", "")) if "reference_answer" in df.columns else ""
        data, used_mock = evaluate_all(q, r, ref)
        v = data.get("verdict", {})
        breakdown = v.get("weighted_score_breakdown", {})
        rows.append({
            "question": q[:60] + ("..." if len(q) > 60 else ""),
            "relevance": breakdown.get("relevance"),
            "accuracy": breakdown.get("accuracy"),
            "hallucination": breakdown.get("hallucination"),
            "completeness": breakdown.get("completeness"),
            "overall_score": v.get("overall_score"),
            "final_verdict": v.get("final_verdict"),
            "quality_gate_passed": v.get("quality_gate_passed"),
        })
        progress.progress((i + 1) / n, text=f"Evaluating row {i + 1}/{n}...")
        time.sleep(0.05)
    progress.empty()
    return {"table": pd.DataFrame(rows), "used_mock": used_mock}


def _render_benchmark_results(results):
    table: pd.DataFrame = results["table"]
    if results.get("used_mock"):
        st.info(
            "⚠️ Backend not reachable — batch results below use demo data so the dashboard "
            "layout can still be reviewed.",
            icon="⚠️",
        )

    st.write("")
    section_label("3. Benchmark Summary")
    avg_overall = table["overall_score"].mean()
    pass_rate = (table["quality_gate_passed"].sum() / len(table)) * 100
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        metric_tile("Rows Evaluated", str(len(table)))
    with m2:
        metric_tile("Avg. Overall Score", f"{avg_overall:.2f}/10")
    with m3:
        metric_tile("Quality Gate Pass Rate", f"{pass_rate:.0f}%")
    with m4:
        metric_tile("Avg. Hallucination Score", f"{table['hallucination'].mean():.2f}/10")

    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        card_open()
        st.markdown("**Score Distribution (Overall)**")
        render_distribution_chart(table["overall_score"].dropna().tolist(), key="dist_benchmark")
        card_close()
    with c2:
        card_open()
        st.markdown("**Average Score by Dimension**")
        avg_scores = {
            "Relevance": table["relevance"].mean(),
            "Accuracy": table["accuracy"].mean(),
            "Hallucination": table["hallucination"].mean(),
            "Completeness": table["completeness"].mean(),
        }
        render_score_bar(avg_scores, key="bar_benchmark")
        card_close()

    st.write("")
    section_label("4. Detailed Results")
    card_open()
    st.dataframe(table, use_container_width=True)
    csv_bytes = table.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Download Evaluation Report (CSV)",
        data=csv_bytes,
        file_name="benchmark_evaluation_report.csv",
        mime="text/csv",
    )
    card_close()
