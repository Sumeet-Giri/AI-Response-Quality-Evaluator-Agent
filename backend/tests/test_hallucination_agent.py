from agents.hallucination_agent import (
    HallucinationDetectionAgent
)

agent = HallucinationDetectionAgent()


test_cases = [

    {
        "response":
        "Paris is the capital of France.",
        "reference":
        "Paris is the capital of France."
    },

    {
        "response":
        "Paris is the capital of France. It is located in Germany.",
        "reference":
        "Paris is the capital of France."
    },

    {
        "response":
        "Python was created by Guido van Rossum. It won a Nobel Prize.",
        "reference":
        "Python was created by Guido van Rossum."
    }

]


for i, test in enumerate(
        test_cases,
        start=1
):

    result = agent.evaluate(
        test["response"],
        test["reference"]
    )

    print(f"\nTest Case {i}")
    print(result)