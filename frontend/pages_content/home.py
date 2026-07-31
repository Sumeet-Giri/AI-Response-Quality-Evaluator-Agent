import streamlit as st
from components.badges import pill, card_open, card_close, section_label
from components.pipeline_viz import render_pipeline


def render():
    # ---------------- HERO ----------------
    st.markdown(
        """
        <div class="hero">
            <div class="hero-title">AI Response Quality Evaluator</div>
            <div class="hero-sub">
                A multi-agent evaluation architecture that independently scores AI-generated
                responses for relevance, factual accuracy, hallucination risk, and completeness —
                then combines them into one consolidated verdict.
            </div>
            <div style="margin-top:18px;">
        """,
        unsafe_allow_html=True,
    )
    for p in ["5 Independent Agents", "FastAPI Backend", "RAG + Semantic Similarity",
              "ChromaDB Vector Store", "Weighted Verdict Engine"]:
        pill(p)
    st.markdown("</div></div>", unsafe_allow_html=True)

    st.write("")
    st.write("")

    # ---------------- KEY METRICS STRIP ----------------
    section_label("At a Glance")
    m1, m2, m3, m4 = st.columns(4)
    for col, label, value in zip(
        [m1, m2, m3, m4],
        ["Evaluation Agents", "Quality Dimensions", "API Endpoints", "Milestone"],
        ["5", "4", "6", "M1"],
    ):
        with col:
            card_open("card-tight")
            st.markdown(f"<div class='metric-label'>{label}</div>"
                         f"<div class='metric-value'>{value}</div>", unsafe_allow_html=True)
            card_close()

    st.write("")

    # ---------------- ARCHITECTURE / PIPELINE ----------------
    section_label("Multi-Agent Evaluation Pipeline")
    card_open()
    render_pipeline()
    st.caption(
        "Each stage is handled by an independent agent with its own scoring logic. "
        "The Verdict Agent consolidates all four dimension scores into a final, weighted report."
    )
    card_close()

    st.write("")

    col1, col2 = st.columns([1.3, 1])

    with col1:
        section_label("Evaluation Dimensions")
        card_open()
        dims = [
            ("Relevance", "25%", "Does the response answer the question? Measured via semantic similarity."),
            ("Accuracy", "35%", "Is the response factually correct against a reference / evidence?"),
            ("Hallucination", "25%", "Are all claims supported, or are some fabricated / unverifiable?"),
            ("Completeness", "15%", "Are all expected aspects of the question covered?"),
        ]
        for name, weight, desc in dims:
            st.markdown(
                f"""
                <div style="display:flex;justify-content:space-between;align-items:flex-start;
                            padding:10px 0;border-bottom:1px solid var(--border)">
                    <div style="max-width:78%">
                        <div style="font-weight:700;color:var(--text-hi)">{name}</div>
                        <div style="font-size:13px;color:var(--text-mid)">{desc}</div>
                    </div>
                    <div class="badge badge-neutral">{weight}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        card_close()

    with col2:
        section_label("Tech Stack")
        card_open()
        stack = {
            "Frontend": "Streamlit + Plotly",
            "Backend": "FastAPI + Pydantic v2",
            "Embeddings": "Sentence-Transformers (TF-IDF fallback)",
            "Vector Store": "ChromaDB (in-memory fallback)",
            "Datasets": "TruthfulQA, SQuAD",
            "Persistence": "SQLite",
            "Eval Frameworks": "RAGAS, TruLens (reference)",
        }
        for k, v in stack.items():
            st.markdown(f"**{k}**  \n<span style='font-size:13px'>{v}</span>", unsafe_allow_html=True)
            st.markdown("<hr class='hr-soft'>", unsafe_allow_html=True)
        card_close()

    st.write("")

    col3, col4 = st.columns(2)
    with col3:
        section_label("Milestone Status")
        card_open()
        milestones = [
            ("Milestone 1 — Core Pipeline & Agents (Jun 30 – Jul 9)", "on"),
            ("Milestone 2 — Evaluation Framework Integration", "pending"),
            ("Milestone 3 — Benchmark Validation & Reporting", "pending"),
        ]
        for label, state in milestones:
            st.markdown(
                f"""<div class="tl-item">
                        <div class="tl-dot {state}"></div>
                        <div>{label}</div>
                    </div>""",
                unsafe_allow_html=True,
            )
        card_close()

    with col4:
        section_label("Team")
        card_open()
        st.markdown(
            """
            <div style="display:flex;gap:14px;align-items:center;">
                <div class="brand-badge" style="width:44px;height:44px;font-size:18px;">AJ</div>
                <div>
                    <div style="font-weight:700;color:var(--text-hi)">Project Lead / Developer</div>
                    <div style="font-size:13px;color:var(--text-mid)">
                        Full pipeline design, agent architecture, RAG integration, and API build.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        card_close()
