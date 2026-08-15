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
                max(0.0, min(1.0, sim)),
                text=f"Semantic Similarity : {sim:.2f}"
            )

            with st.expander("Reasoning"):

                st.write(
                    data.get("reasoning", "No reasoning available.")
                )


# ===================================================
# ACCURACY CARD
# ===================================================

def _rag_status_line(rag_info: dict | None):
    """
    Renders a one-line, honest explanation of where the reference text
    used for Accuracy/Hallucination scoring came from. Previously there
    was no visibility into this at all -- an auto-retrieved passage (or,
    worse, an empty reference) was shown with no context, which looked
    like a bug rather than an expected consequence of not supplying a
    reference answer.
    """
    if not rag_info:
        return

    source = rag_info.get("source")

    if source == "user_supplied":
        return  # nothing surprising here -- the evidence below is exactly what was typed in.

    if source == "retrieved":
        distance = rag_info.get("similarity_distance")
        similarity_pct = f"{(1 - distance) * 100:.0f}%" if isinstance(distance, (int, float)) else "unknown"
        st.info(
            f"🔎 No reference answer was supplied — this reference was "
            f"auto-retrieved from the knowledge base (estimated relevance: {similarity_pct}).",
            icon="🔎",
        )
        return

    # source == "none"
    st.warning(
        "⚠️ No reference answer was supplied, and nothing sufficiently "
        "relevant was found in the knowledge base for this question. "
        "Accuracy and Hallucination below are scored against an empty "
        "reference, which will generally score low regardless of how "
        "correct the response actually is — provide a reference answer "
        "for a meaningful score on these two dimensions.",
        icon="⚠️",
    )


def accuracy_card(data, rag_info=None):

    with card():

        section_label("Accuracy Agent")
        _rag_status_line(rag_info)

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
            unverified = bool(rag_info) and rag_info.get("source") == "none"

            if unverified:
                badge_text, badge_kind = "Unverified — No Reference Available", "neutral"
            elif correct:
                badge_text, badge_kind = "Factually Correct ✓", "good"
            else:
                badge_text, badge_kind = "Factual Issues Found", "bad"

            st.markdown(
                badge_html(badge_text, badge_kind),
                unsafe_allow_html=True
            )

            sim = data.get(
                "semantic_similarity",
                0
            )

            st.progress(
                max(0.0, min(1.0, sim)),
                text=f"Semantic Similarity : {sim:.2f}"
            )

            evidence = data.get(
                "evidence",
                []
            )
            evidence = [e for e in evidence if e and e.strip()]

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

def hallucination_card(data, rag_info=None):

    with card():

        section_label(
            "Hallucination Detection Agent"
        )
        _rag_status_line(rag_info)

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
            unverified = bool(rag_info) and rag_info.get("source") == "none"

            if unverified:
                risk_kind, risk_text = "neutral", "Unverified — No Reference Available"
            elif not hallucinated:
                risk_kind, risk_text = "good", "Low Risk"
            else:
                risk_kind, risk_text = "warn", f"{len(hallucinated)} Unsupported Claim(s)"

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