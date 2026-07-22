import streamlit as st

from utils.api import (
    validate_relevance,
    validate_accuracy,
    validate_hallucination,
    validate_all
)


# ==================================================
# PAGE TITLE
# ==================================================

st.title("Benchmark Validation")
st.markdown("---")

st.write(
    """
Validate the performance of the Relevance,
Accuracy and Hallucination Agents using
predefined benchmark test cases.
"""
)

st.markdown("---")


# ==================================================
# BUTTONS
# ==================================================

col1, col2 = st.columns(2)

with col1:

    relevance_button = st.button(
        "Validate Relevance Agent",
        use_container_width=True
    )

    hallucination_button = st.button(
        "Validate Hallucination Agent",
        use_container_width=True
    )

with col2:

    accuracy_button = st.button(
        "Validate Accuracy Agent",
        use_container_width=True
    )

    all_button = st.button(
        "Validate All Agents",
        use_container_width=True
    )

st.markdown("---")


# ==================================================
# RELEVANCE VALIDATION
# ==================================================

if relevance_button:

    result = validate_relevance()

    st.header("Relevance Agent Validation")

    total_tests = len(result)

    st.metric("Total Test Cases", total_tests)

    st.markdown("---")

    for i, test_case in enumerate(result, start=1):

        with st.expander(f"Test Case {i}"):

            st.write("### Question")
            st.write(test_case["question"])

            st.write("### Response")
            st.write(test_case["response"])

            score = test_case["result"]["score"]

            st.write(f"### Score : {score} / 10")

            st.write(
                f"Semantic Similarity : "
                f"{round(test_case['result']['semantic_similarity'],4)}"
            )

            topic_match = test_case["result"]["topic_match"]

            if topic_match:
                st.success("Topic Match : TRUE")
            else:
                st.error("Topic Match : FALSE")

            st.info(test_case["result"]["reasoning"])



# ==================================================
# ACCURACY VALIDATION
# ==================================================

if accuracy_button:

    result = validate_accuracy()

    st.header("Accuracy Agent Validation")

    total_tests = len(result)

    st.metric("Total Test Cases", total_tests)

    st.markdown("---")

    for i, test_case in enumerate(result, start=1):

        with st.expander(f"Test Case {i}"):

            st.write("### Response")
            st.write(test_case["response"])

            st.write("### Reference Answer")
            st.write(test_case["reference_answer"])

            score = test_case["result"]["score"]

            st.write(f"### Score : {score} / 10")

            st.write(
                f"Semantic Similarity : "
                f"{round(test_case['result']['semantic_similarity'],4)}"
            )

            if test_case["result"]["factually_correct"]:
                st.success("Factually Correct : TRUE")
            else:
                st.error("Factually Correct : FALSE")


            st.write("### Supporting Evidence")

            for evidence in test_case["result"]["evidence"]:
                st.success(evidence)


            st.info(test_case["result"]["reasoning"])



# ==================================================
# HALLUCINATION VALIDATION
# ==================================================

if hallucination_button:

    result = validate_hallucination()

    st.header("Hallucination Agent Validation")

    total_tests = len(result)

    st.metric("Total Test Cases", total_tests)

    st.markdown("---")

    for i, test_case in enumerate(result, start=1):

        with st.expander(f"Test Case {i}"):

            score = test_case["result"]["hallucination_score"]

            st.write(
                f"### Hallucination Score : {score} / 10"
            )

            st.write("### Supported Claims")

            for claim in test_case["result"]["supported_claims"]:
                st.success(claim)


            st.write("### Hallucinated Claims")

            if len(
                test_case["result"]["hallucinated_claims"]
            ) == 0:

                st.success("No hallucinations detected.")

            else:

                for claim in test_case["result"]["hallucinated_claims"]:
                    st.error(claim)


            st.info(test_case["result"]["reasoning"])



# ==================================================
# VALIDATE ALL AGENTS
# ==================================================

if all_button:

    result = validate_all()

    st.header("Validation Summary")

    relevance_tests = result["relevance_validation"]
    accuracy_tests = result["accuracy_validation"]
    hallucination_tests = result["hallucination_validation"]


    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Relevance Tests",
            len(relevance_tests)
        )

    with col2:
        st.metric(
            "Accuracy Tests",
            len(accuracy_tests)
        )

    with col3:
        st.metric(
            "Hallucination Tests",
            len(hallucination_tests)
        )


    st.success(
        "All validation test cases executed successfully."
    )

    st.markdown("---")


    # RELEVANCE SUMMARY

    st.subheader("Relevance Agent Results")

    for i, test_case in enumerate(relevance_tests, start=1):

        with st.expander(f"Relevance Test Case {i}"):

            st.write(
                f"Score : {test_case['result']['score']} / 10"
            )

            st.write(
                test_case["result"]["reasoning"]
            )


    # ACCURACY SUMMARY

    st.subheader("Accuracy Agent Results")

    for i, test_case in enumerate(accuracy_tests, start=1):

        with st.expander(f"Accuracy Test Case {i}"):

            st.write(
                f"Score : {test_case['result']['score']} / 10"
            )

            st.write(
                test_case["result"]["reasoning"]
            )


    # HALLUCINATION SUMMARY

    st.subheader("Hallucination Agent Results")

    for i, test_case in enumerate(
            hallucination_tests,
            start=1):

        with st.expander(
                f"Hallucination Test Case {i}"):

            st.write(
                f"Hallucination Score : "
                f"{test_case['result']['hallucination_score']} / 10"
            )

            st.write(
                test_case["result"]["reasoning"]
            )