import streamlit as st

# Import Components

from components.relevance_card import show_relevance_card
from components.accuracy_card import show_accuracy_card
from components.hallucination_card import show_hallucination_card
from components.summary import show_final_summary

# API Function
from utils.api import evaluate_response


# ==================================================
# PAGE TITLE
# ==================================================

st.title("Single Response Evaluation")
st.markdown("---")


# ==================================================
# INPUT SECTION
# ==================================================

st.header("Input Details")

question = st.text_area(
    "Question *",
    placeholder="Enter the question here...",
    height=120
)

response = st.text_area(
    "AI Response *",
    placeholder="Enter the AI generated response here...",
    height=200
)

reference_answer = st.text_area(
    "Reference Answer (Optional)",
    placeholder="Enter reference answer if available...",
    height=150
)


# ==================================================
# BUTTON SECTION
# ==================================================

col1, col2 = st.columns(2)

with col1:

    evaluate_button = st.button(
        "Evaluate Response",
        use_container_width=True
    )

with col2:

    reset_button = st.button(
        "Reset",
        use_container_width=True
    )


st.markdown("---")


# ==================================================
# RESET BUTTON
# ==================================================

if reset_button:
    st.rerun()


# ==================================================
# EVALUATE BUTTON
# ==================================================

if evaluate_button:

    # Input Validation

    if not question.strip() or not response.strip():

        st.error(
            "Please provide both Question and AI Response before evaluation."
        )

    else:

        # ------------------------------------------
        # CALL FASTAPI ENDPOINT
        # ------------------------------------------

        result = evaluate_response(
            question,
            response,
            reference_answer
        )

        # ------------------------------------------
        # ERROR HANDLING
        # ------------------------------------------

        if "error" in result:

            st.error(result["error"])

        else:

            st.success(
                "AI Response evaluated successfully using all three evaluation agents."
            )

            st.markdown("---")

            # ------------------------------------------
            # EXTRACT API RESULTS
            # ------------------------------------------

            relevance_result = result["relevance"]

            accuracy_result = result["accuracy"]

            hallucination_result = result["hallucination"]

            # ==================================================
            # RELEVANCE AGENT RESULT
            # ==================================================

            st.subheader("Relevance Agent Result")

            show_relevance_card(

                score=relevance_result["score"],

                semantic_similarity=
                relevance_result["semantic_similarity"],

                topic_match=
                relevance_result["topic_match"],

                reasoning=
                relevance_result["reasoning"]

            )

            st.markdown("---")

            # ==================================================
            # ACCURACY AGENT RESULT
            # ==================================================

            st.subheader("Accuracy Agent Result")

            show_accuracy_card(

                score=
                accuracy_result["score"],

                semantic_similarity=
                accuracy_result["semantic_similarity"],

                factual_correctness=
                accuracy_result["factually_correct"],

                evidence=
                accuracy_result["evidence"],

                reasoning=
                accuracy_result["reasoning"]

            )

            st.markdown("---")

            # ==================================================
            # HALLUCINATION AGENT RESULT
            # ==================================================

            st.subheader("Hallucination Agent Result")

            show_hallucination_card(

                score=
                hallucination_result["hallucination_score"],

                supported_claims=
                hallucination_result["supported_claims"],

                hallucinated_claims=
                hallucination_result["hallucinated_claims"],

                reasoning=
                hallucination_result["reasoning"]

            )

            st.markdown("---")

            # ==================================================
            # FINAL EVALUATION SUMMARY
            # ==================================================

            avg_score = (

                relevance_result["score"]
                + accuracy_result["score"]
                + hallucination_result["hallucination_score"]

            ) / 3

            if avg_score >= 8:
                quality = "EXCELLENT"

            elif avg_score >= 6:
                quality = "GOOD"

            elif avg_score >= 4:
                quality = "AVERAGE"

            else:
                quality = "POOR"

            verdict = (

                "The AI response has been successfully evaluated "
                "based on relevance, factual accuracy and "
                "hallucination detection."

            )

            st.subheader("Final Evaluation Summary")

            show_final_summary(

                relevance_score=
                relevance_result["score"],

                accuracy_score=
                accuracy_result["score"],

                hallucination_score=
                hallucination_result["hallucination_score"],

                quality=quality,

                verdict=verdict

            )


# ==================================================
# EVALUATION PIPELINE
# ==================================================

st.markdown("---")

st.header("Evaluation Pipeline")

st.info(
    """
Question

↓

AI Response

↓

Relevance Judge Agent

↓

Accuracy Judge Agent

↓

Hallucination Detection Agent

↓

Final Evaluation Summary
"""
)