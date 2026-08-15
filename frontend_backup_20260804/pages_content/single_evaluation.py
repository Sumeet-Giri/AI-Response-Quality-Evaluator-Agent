import time
import streamlit as st

from components.badges import card_open, card_close, section_label
from components.pipeline_viz import render_pipeline
from components.charts import render_radar_chart, render_score_bar
from components.result_cards import (
    relevance_card, accuracy_card, hallucination_card, completeness_card, verdict_card,
)
from utils.api_client import evaluate_all


def render():
    st.markdown("<div class='hero-title' style='font-size:30px'>Single Evaluation</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hero-sub'>Submit a question, an AI-generated response, and an optional "
        "reference answer to run the full multi-agent evaluation pipeline.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    # ---------------- INPUT CARD ----------------
    section_label("Evaluation Input")
    card_open()
    question = st.text_area("❓ Question", placeholder="e.g. What causes rainbows to form?", height=90)
    response_text = st.text_area(
        "🤖 AI Generated Response",
        placeholder="Paste the AI-generated response to be evaluated...",
        height=140,
    )
    reference = st.text_area(
        "📖 Reference Answer (optional)",
        placeholder="Provide a ground-truth / reference answer to improve accuracy scoring...",
        height=90,
    )

    b1, b2, _ = st.columns([1, 1, 4])
    with b1:
        run = st.button("🚀 Evaluate Response", use_container_width=True)
    with b2:
        reset = st.button("↺ Reset", use_container_width=True)
    card_close()

    if reset:
        st.session_state.pop("eval_result", None)
        st.rerun()

    if run:
        if not question.strip() or not response_text.strip():
            st.warning("Please provide at least a Question and an AI Response before evaluating.")
        else:
            _run_pipeline_animation()
            data, used_mock = evaluate_all(question, response_text, reference)
            st.session_state["eval_result"] = data
            st.session_state["eval_used_mock"] = used_mock

    if "eval_result" in st.session_state:
        st.write("")
        if st.session_state.get("eval_used_mock"):
            st.info(
                "⚠️ Backend not reachable — showing demo data so the interface can still be reviewed. "
                "Connect the FastAPI backend to see real evaluation results.",
                icon="⚠️",
            )
        _render_results(st.session_state["eval_result"])


def _run_pipeline_animation():
    section_label("Pipeline Execution")
    placeholder = st.empty()
    stages = ["Question", "AI Response", "Relevance", "Accuracy", "Hallucination", "Completeness", "Verdict", "Final Report"]
    for i in range(len(stages)):
        with placeholder.container():
            card_open()
            render_pipeline(stages, completed_upto=i - 1, active_index=i)
            card_close()
        time.sleep(0.18)
    with placeholder.container():
        card_open()
        render_pipeline(stages, completed_upto=len(stages) - 1, active_index=-1)
        card_close()


def _render_results(data: dict):
    section_label("Per-Dimension Results")
    relevance_card(data.get("relevance", {}))
    accuracy_card(data.get("accuracy", {}))
    hallucination_card(data.get("hallucination", {}))
    completeness_card(data.get("completeness", {}))

    st.write("")
    verdict_card(data.get("verdict", {}))

    # ---------------- FINAL REPORT VISUALS ----------------
    st.write("")
    section_label("Final Evaluation Report")

    breakdown = data.get("verdict", {}).get("weighted_score_breakdown", {})
    if breakdown:
        chart_scores = {k.capitalize(): v for k, v in breakdown.items()}
        c1, c2 = st.columns(2)
        with c1:
            card_open()
            st.markdown("**Agent Score Radar**")
            render_radar_chart(chart_scores, key="radar_single")
            card_close()
        with c2:
            card_open()
            st.markdown("**Agent Score Comparison**")
            render_score_bar(chart_scores, key="bar_single")
            card_close()

    card_open()
    st.markdown("**Performance Summary**")
    v = data.get("verdict", {})
    st.markdown(
        f"""
        - **Overall Score:** {v.get('overall_score', '—')}/10
        - **Final Verdict:** {v.get('final_verdict', '—')}
        - **Quality Gate:** {"✅ Passed" if v.get('quality_gate_passed') else "❌ Failed"}
        """
    )
    st.write(v.get("consolidated_reasoning", ""))
    card_close()
