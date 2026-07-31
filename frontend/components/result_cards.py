import streamlit as st

from components.score_ring import render_score_ring
from components.badges import badge_html, section_label, card


# ===================================================
# RELEVANCE CARD
# ===================================================

def relevance_card(data):

    with card():

        section_label("Relevance Agent")

        c1, c2 = st.columns([1, 2])

        with c1:
            render_score_ring(
                data.get("score", 0),
                "Relevance Score",
                key="ring_relevance"
            )

        with c2:

            sim = data.get("semantic_similarity", 0)
            match = data.get("topic_match", False)

            st.markdown(
                badge_html(
                    "Topic Match ✓"
                    if match else
                    "Topic Mismatch",

                    "good"
                    if match else
                    "bad"
                ),
                unsafe_allow_html=True
            )

            st.progress(
                min(1.0, sim),
                text=f"Semantic Similarity : {sim:.2f}"
            )

            with st.expander("Reasoning"):

                st.write(
                    data.get("reasoning", "No reasoning available.")
                )


# ===================================================
# ACCURACY CARD
# ===================================================

def accuracy_card(data):

    with card():

        section_label("Accuracy Agent")

        c1, c2 = st.columns([1, 2])

        with c1:

            render_score_ring(
                data.get("score", 0),
                "Accuracy Score",
                key="ring_accuracy"
            )

        with c2:

            correct = data.get(
                "factually_correct",
                False
            )

            st.markdown(
                badge_html(
                    "Factually Correct ✓"
                    if correct else
                    "Factual Issues Found",

                    "good"
                    if correct else
                    "bad"
                ),
                unsafe_allow_html=True
            )

            sim = data.get(
                "semantic_similarity",
                0
            )

            st.progress(
                min(1.0, sim),
                text=f"Semantic Similarity : {sim:.2f}"
            )

            evidence = data.get(
                "evidence",
                []
            )

            if evidence:

                st.caption("Supporting Evidence")

                for item in evidence:

                    st.markdown(f"- {item}")

            with st.expander("Reasoning"):

                st.write(
                    data.get(
                        "reasoning",
                        "No reasoning available."
                    )
                )


# ===================================================
# HALLUCINATION CARD
# ===================================================

def hallucination_card(data):

    with card():

        section_label(
            "Hallucination Detection Agent"
        )

        c1, c2 = st.columns([1, 2])

        with c1:

            render_score_ring(
                data.get("score", 0),
                "Hallucination-Free Score",
                key="ring_hallucination"
            )

        with c2:

            hallucinated = data.get(
                "hallucinated_claims",
                []
            )

            risk_kind = (
                "good"
                if not hallucinated
                else "warn"
            )

            risk_text = (
                "Low Risk"
                if not hallucinated
                else f"{len(hallucinated)} Unsupported Claim(s)"
            )

            st.markdown(
                badge_html(
                    risk_text,
                    risk_kind
                ),
                unsafe_allow_html=True
            )

            supported = data.get(
                "supported_claims",
                []
            )

            col1, col2 = st.columns(2)

            with col1:

                st.caption(
                    f"Supported Claims ({len(supported)})"
                )

                for item in supported:

                    st.markdown(
                        f"- {item}"
                    )

            with col2:

                st.caption(
                    f"Hallucinated Claims ({len(hallucinated)})"
                )

                if hallucinated:

                    for item in hallucinated:

                        st.markdown(
                            f"- {item}"
                        )

                else:

                    st.markdown(
                        "_None detected_"
                    )

            with st.expander("Reasoning"):

                st.write(
                    data.get(
                        "reasoning",
                        "No reasoning available."
                    )
                )


# ===================================================
# COMPLETENESS CARD
# ===================================================

def completeness_card(data):

    with card():

        section_label(
            "Completeness Agent"
        )

        c1, c2 = st.columns([1, 2])

        with c1:

            render_score_ring(
                data.get("score", 0),
                "Completeness Score",
                key="ring_completeness"
            )

        with c2:

            coverage = data.get(
                "coverage_percentage",
                0
            )

            total = data.get(
                "total_aspects",
                0
            )

            covered = data.get(
                "covered_aspects",
                []
            )

            st.progress(
                coverage / 100,
                text=f"Coverage : {coverage:.1f}% ({len(covered)}/{total})"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.caption("Covered Aspects")

                for item in covered:

                    st.markdown(
                        f"- {item}"
                    )

            with col2:

                missing = data.get(
                    "missing_aspects",
                    []
                )

                st.caption("Missing Aspects")

                if missing:

                    for item in missing:

                        st.markdown(
                            f"- {item}"
                        )

                else:

                    st.markdown(
                        "_None - Fully Covered_"
                    )

            with st.expander("Reasoning"):

                st.write(
                    data.get(
                        "reasoning",
                        "No reasoning available."
                    )
                )


# ===================================================
# VERDICT CARD
# ===================================================

def verdict_card(data):

    with card():

        section_label(
            "Verdict Agent - Final Evaluation"
        )

        c1, c2 = st.columns([1, 2])

        with c1:

            render_score_ring(
                data.get(
                    "overall_score",
                    0
                ),
                "Overall Score",
                key="ring_verdict",
                size=210
            )

        with c2:

            strengths = data.get(
                "strengths",
                []
            )

            weaknesses = data.get(
                "weaknesses",
                []
            )

            col1, col2 = st.columns(2)

            with col1:

                st.caption("Strengths")

                for item in strengths:

                    st.markdown(
                        f"- {item}"
                    )

            with col2:

                st.caption("Weaknesses")

                if weaknesses:

                    for item in weaknesses:

                        st.markdown(
                            f"- {item}"
                        )

                else:

                    st.markdown(
                        "_None identified_"
                    )

            with st.expander(
                    "Consolidated Reasoning",
                    expanded=True):

                st.write(
                    data.get(
                        "consolidated_reasoning",
                        "No reasoning available."
                    )
                )