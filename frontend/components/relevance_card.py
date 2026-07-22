import streamlit as st


def show_relevance_card(
        score,
        semantic_similarity,
        topic_match,
        reasoning
):

    st.subheader("Relevance Judge Agent")

    st.metric(
        label="Relevance Score",
        value=f"{score}/10"
    )

    st.metric(
        label="Semantic Similarity",
        value=semantic_similarity
    )

    if topic_match:
        st.success("Topic Match : TRUE")
    else:
        st.error("Topic Match : FALSE")

    st.write("Reasoning")

    st.info(reasoning)

    st.progress(score / 10)

    st.markdown("---")