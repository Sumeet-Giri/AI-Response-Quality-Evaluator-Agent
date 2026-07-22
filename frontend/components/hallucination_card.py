import streamlit as st


def show_hallucination_card(
        score,
        supported_claims,
        hallucinated_claims,
        reasoning
):

    st.subheader("Hallucination Detection Agent")

    st.metric(
        label="Hallucination Score",
        value=f"{score}/10"
    )


    st.write("Supported Claims")

    for claim in supported_claims:
        st.success(claim)


    st.write("Hallucinated Claims")

    for claim in hallucinated_claims:
        st.warning(claim)


    st.write("Reasoning")

    st.info(reasoning)

    st.progress(score / 10)

    st.markdown("---")