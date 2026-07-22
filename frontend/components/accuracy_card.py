import streamlit as st


def show_accuracy_card(
        score,
        semantic_similarity,
        factual_correctness,
        evidence,
        reasoning
):

    st.subheader("Accuracy Judge Agent")

    st.metric(
        label="Accuracy Score",
        value=f"{score}/10"
    )

    st.metric(
        label="Semantic Similarity",
        value=semantic_similarity
    )


    if factual_correctness:
        st.success("Factually Correct : TRUE")

    else:
        st.error("Factually Correct : FALSE")


    st.write("Supporting Evidence")

    st.info(evidence)


    st.write("Reasoning")

    st.info(reasoning)


    st.progress(score / 10)

    st.markdown("---")