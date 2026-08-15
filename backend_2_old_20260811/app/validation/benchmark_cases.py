# validation/benchmark_cases.py


# -------------------------
# RELEVANCE TEST CASES
# -------------------------

RELEVANCE_TEST_CASES = [

    {
        "question": "What is the capital of France?",
        "response": "The capital of France is Paris."
    },

    {
        "question": "What is Machine Learning?",
        "response": "I like watching cricket on weekends."
    },

    {
        "question": "Explain the water cycle.",
        "response": "Water evaporates from the Earth's surface."
    }

]


# -------------------------
# ACCURACY TEST CASES
# -------------------------

ACCURACY_TEST_CASES = [

    {
        "response": "The capital of France is Paris.",
        "reference_answer": "Paris is the capital of France."
    },

    {
        "response": "HTTP is a protocol used for communication on the web.",
        "reference_answer": "HTTP is a protocol used for communication on the web."
    },

    {
        "response": "Machine Learning is a subset of Artificial Intelligence.",
        "reference_answer": "Machine Learning is a subset of Artificial Intelligence."
    }

]


# -------------------------
# HALLUCINATION TEST CASES
# -------------------------

HALLUCINATION_TEST_CASES = [

    {
        "response": "Paris is the capital of France.",
        "reference_answer": "Paris is the capital of France."
    },

    {
        "response": "Paris is the capital of France. It is located in Germany.",
        "reference_answer": "Paris is the capital of France."
    },

    {
        "response": "Python was created by Guido van Rossum. It won a Nobel Prize.",
        "reference_answer": "Python was created by Guido van Rossum."
    }

]


# -------------------------
# COMPLETENESS TEST CASES
# -------------------------
# Added to close a gap identified in architecture review: Milestone 3
# introduced the Completeness agent but the benchmark validator was never
# extended to cover it, so `/validation/all` didn't actually validate the
# full pipeline that ships today.

COMPLETENESS_TEST_CASES = [

    {
        "question": "What is Machine Learning and what are its types?",
        "response": (
            "Machine Learning is a subset of Artificial Intelligence. "
            "There are different types, including supervised and "
            "unsupervised learning."
        )
    },

    {
        "question": "What are the advantages and disadvantages of cloud computing?",
        "response": "Cloud computing is scalable and cost-effective."
    },

    {
        "question": "Explain the steps involved in the software development lifecycle.",
        "response": (
            "The process includes several steps: requirement gathering, "
            "design, implementation, testing, and deployment."
        )
    }

]