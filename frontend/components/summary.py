import streamlit as st


def show_final_summary(
        relevance_score,
        accuracy_score,
        hallucination_score,
        verdict,
        quality
):

    st.header("FINAL EVALUATION SUMMARY")


    st.metric(
        "Relevance Score",
        f"{relevance_score}/10"
    )


    st.metric(
        "Accuracy Score",
        f"{accuracy_score}/10"
    )


    st.metric(
        "Hallucination Score",
        f"{hallucination_score}/10"
    )


    st.markdown("---")


    st.subheader("Overall Response Quality")

    if quality == "EXCELLENT":
        st.success(quality)

    elif quality == "GOOD":
        st.success(quality)

    elif quality == "AVERAGE":
        st.warning(quality)

    else:
        st.error(quality)


    st.subheader("Suggested Verdict")

    st.info(verdict)

    st.markdown("---")