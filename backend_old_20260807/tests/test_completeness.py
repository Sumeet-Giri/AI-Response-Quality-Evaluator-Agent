from agents.completeness_agent import CompletenessJudge


def print_result(result):
    print("\n" + "=" * 60)
    print(f"Completeness Score      : {result.completeness_score}/10")
    print(f"Coverage Percentage    : {result.coverage_percentage}%")
    print(f"Total Aspects          : {result.total_aspects}")
    print()

    print("Extracted Aspects:")
    for aspect in result.extracted_aspects:
        print(f"  - {aspect}")

    print()

    print("Covered Aspects:")
    for aspect in result.covered_aspects:
        print(f"  - {aspect}")

    print()

    print("Missing Aspects:")
    for aspect in result.missing_aspects:
        print(f"  - {aspect}")

    print()

    print("Reasoning:")
    print(result.reasoning)
    print("=" * 60)


def run_tests():

    agent = CompletenessJudge()

    test_cases = [

        # Test Case 1
        {
            "title": "Complete Response",
            "question": "What is Machine Learning? Explain its types and applications.",
            "response": """
            Machine Learning is a branch of Artificial Intelligence.
            It includes supervised, unsupervised and reinforcement learning.
            It is used in healthcare, recommendation systems and self-driving cars.
            """
        },

        # Test Case 2
        {
            "title": "Partially Complete Response",
            "question": "What is Machine Learning? Explain its types and applications.",
            "response": """
            Machine Learning is a branch of Artificial Intelligence.
            It includes supervised and unsupervised learning.
            """
        },

        # Test Case 3
        {
            "title": "Only Definition",
            "question": "What is Machine Learning? Explain its types and applications.",
            "response": """
            Machine Learning is a subset of Artificial Intelligence.
            """
        },

        # Test Case 4
        {
            "title": "Advantages and Disadvantages",
            "question": "Explain advantages and disadvantages of cloud computing.",
            "response": """
            Cloud computing offers scalability, flexibility and cost savings.
            """
        },

        # Test Case 5
        {
            "title": "Features and Applications",
            "question": "Explain features and applications of Python.",
            "response": """
            Python is easy to learn and highly readable.
            It is used in web development and machine learning.
            """
        },

        # Test Case 6
        {
            "title": "Compare Question",
            "question": "Compare TCP and UDP.",
            "response": """
            TCP is connection-oriented whereas UDP is connectionless.
            """
        },

        # Test Case 7
        {
            "title": "Empty Response",
            "question": "Explain Artificial Intelligence.",
            "response": ""
        },

        # Test Case 8
        {
            "title": "Irrelevant Response",
            "question": "Explain applications of Blockchain.",
            "response": """
            Football is the most popular sport in the world.
            """
        },

        # Test Case 9
        {
            "title": "Components Question",
            "question": "Explain CPU and its components.",
            "response": """
            CPU is the brain of the computer.
            Its components are ALU, Control Unit and Registers.
            """
        },

        # Test Case 10
        {
            "title": "Working Question",
            "question": "Explain the working of DNS.",
            "response": """
            DNS converts domain names into IP addresses.
            """
        }

    ]

    for test in test_cases:

        print("\n\n")
        print(f"TEST CASE : {test['title']}")

        result = agent.evaluate(
            question=test["question"],
            response=test["response"]
        )

        print_result(result)


if __name__ == "__main__":
    run_tests()