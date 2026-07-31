import streamlit as st
from components.badges import card_open, card_close, section_label, badge_html


def render():
    st.markdown("<div class='hero-title' style='font-size:30px'>About the Project</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hero-sub'>A structured, multi-agent system for evaluating the quality of "
        "AI-generated responses — built for reliability, transparency, and reproducibility.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    # Problem statement / objective
    c1, c2 = st.columns(2)
    with c1:
        section_label("Problem Statement")
        card_open()
        st.write(
            "As LLMs are deployed in production systems, there is no single reliable signal to "
            "confirm a generated response is relevant, factually correct, free of hallucinations, "
            "and complete. Manual review does not scale, and generic accuracy metrics fail to "
            "capture the multi-dimensional nature of response quality."
        )
        card_close()
    with c2:
        section_label("Project Objective")
        card_open()
        st.write(
            "Build an automated, multi-agent evaluation system where each quality dimension is "
            "assessed independently and then consolidated into a single, explainable verdict — "
            "with reasoning attached to every score, so results can be audited, not just trusted."
        )
        card_close()

    st.write("")
    section_label("System Architecture")
    card_open()
    st.markdown(
        """
```
                        ┌─────────────────────────┐
                        │   Streamlit Frontend     │
                        │  (this dashboard layer)  │
                        └────────────┬─────────────┘
                                     │ REST calls
                        ┌────────────▼─────────────┐
                        │      FastAPI Backend      │
                        │   app/main.py + routers    │
                        └────────────┬─────────────┘
                                     │
      ┌────────────┬─────────────┬───┴──────────┬──────────────┐
      ▼            ▼             ▼              ▼              ▼
 Relevance     Accuracy     Hallucination   Completeness    Verdict
  Agent         Agent          Agent           Agent         Agent
      │            │             │              │              │
      └────────────┴─────────────┴──────────────┴──────────────┘
                                     │
                     Sentence-Transformers · RAG · ChromaDB
```
        """
    )
    card_close()

    st.write("")
    section_label("Agent Descriptions")
    agents = [
        ("Relevance Agent", "Compares question and response via semantic similarity to confirm topical alignment.", "25%"),
        ("Accuracy Agent", "Validates factual correctness of the response against reference / evidence context.", "35%"),
        ("Hallucination Agent", "Flags claims not supported by retrieved context or reference evidence.", "25%"),
        ("Completeness Agent", "Extracts expected aspects of the question and checks coverage in the response.", "15%"),
        ("Verdict Agent", "Combines all four weighted scores into one final, explainable verdict.", "brain"),
    ]
    for name, desc, weight in agents:
        card_open("card-tight card-hover")
        cc1, cc2 = st.columns([4, 1])
        with cc1:
            st.markdown(f"**{name}**")
            st.caption(desc)
        with cc2:
            if weight == "brain":
                st.markdown(badge_html("Consolidator", "neutral"), unsafe_allow_html=True)
            else:
                st.markdown(badge_html(f"Weight {weight}", "neutral"), unsafe_allow_html=True)
        card_close()

    st.write("")
    c3, c4 = st.columns(2)
    with c3:
        section_label("Tech Stack")
        card_open()
        st.markdown(
            """
            **Frontend:** Streamlit, Plotly
            **Backend:** FastAPI, Pydantic v2 (request/response schemas)
            **AI Components:** Sentence-Transformers, semantic similarity, RAG pipeline
            **Vector Store:** ChromaDB (in-memory numpy fallback)
            **Datasets:** TruthfulQA, SQuAD (Hugging Face Hub, offline fallback)
            **Persistence:** SQLite
            **Testing:** pytest (per-agent unit tests)
            """
        )
        card_close()
    with c4:
        section_label("API Architecture")
        card_open()
        st.code(
            "POST /evaluate/relevance\n"
            "POST /evaluate/accuracy\n"
            "POST /evaluate/hallucination\n"
            "POST /evaluate/completeness\n"
            "POST /evaluate/verdict\n"
            "POST /evaluate/all   # runs full pipeline, returns all 5 reports",
            language="text",
        )
        card_close()

    st.write("")
    section_label("Workflow Diagram")
    card_open()
    st.markdown(
        "Question → AI Response → Relevance → Accuracy → Hallucination → "
        "Completeness → Verdict → **Final Evaluation Report**"
    )
    card_close()

    st.write("")
    section_label("Future Scope")
    card_open()
    st.markdown(
        """
        - Integrate **RAGAS** and **TruLens** as secondary validation layers alongside custom agents
        - Add batch / benchmark-level dashboards with historical trend tracking
        - Support pluggable LLM judges (in addition to embedding-based scoring)
        - Add user feedback loop to calibrate agent weights over time
        - Export shareable PDF evaluation reports directly from the dashboard
        """
    )
    card_close()
