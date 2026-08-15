from agents.accuracy_agent import AccuracyJudgeAgent


agent = AccuracyJudgeAgent()


test_cases = [
    {
        "response": "The capital of France is Paris.",
        "reference": "Paris is the capital of France."
    },
    {
        "response": "The capital of France is London.",
        "reference": "Paris is the capital of France."
    },
    {
        "response": "HTTP is used for web communication.",
        "reference": "HTTP is a protocol used for communication on the web."
    },
    {
        "response": "Machine Learning is a subset of AI.",
        "reference": "Machine Learning is a subset of Artificial Intelligence."
    },
    {
        "response": "The Sun revolves around the Earth.",
        "reference": "The Earth revolves around the Sun."
    }
]


for i, test in enumerate(test_cases, start=1):

    result = agent.evaluate(
        test["response"],
        test["reference"]
    )

    print(f"\nTest Case {i}")
    print(result)