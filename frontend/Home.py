import streamlit as st

# Page configuration
st.set_page_config(
    page_title="AI Response Quality Evaluator Agent",
    page_icon="🤖",
    layout="wide"
)

# Title Section
st.title("🤖 AI Response Quality Evaluator Agent")
st.markdown("---")

# Welcome Section
st.header("Welcome!")

st.info(
    """
    Evaluate AI-generated responses using a Multi-Agent Evaluation Pipeline.
    """
)

# Agents Section
st.subheader("Evaluation Agents")

col1, col2, col3 = st.columns(3)

with col1:
    st.success("Relevance Judge Agent")

with col2:
    st.success("Accuracy Judge Agent")

with col3:
    st.success("Hallucination Detection Agent")

st.markdown("---")

# Project Overview Section

st.subheader("How the Evaluation Works")

st.markdown(
    """
    ```text
                  Question
                      ↓
                 AI Response
                      ↓
             Multi-Agent Evaluation
                      ↓
            Relevance | Accuracy | Hallucination
                      ↓
                Final Evaluation Summary
    ```
    """
)

st.markdown("---")


# Features Section

st.subheader("Available Features")

feature1, feature2 = st.columns(2)

with feature1:
    st.info(
        """
        ### Single Response Evaluation

        Evaluate a single AI-generated response using all three evaluation agents.
        """
    )

with feature2:
    st.info(
        """
        ### Benchmark Validation

        Validate individual evaluation agents using predefined test cases.
        """
    )


st.markdown("---")


# Footer Section

st.caption(
    "AI Response Quality Evaluator Agent | Multi-Agent Evaluation Framework"
)