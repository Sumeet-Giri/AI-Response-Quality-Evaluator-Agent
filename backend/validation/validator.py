from agents.relevance_agent import RelevanceJudgeAgent
from agents.accuracy_agent import AccuracyJudgeAgent
from agents.hallucination_agent import HallucinationDetectionAgent


class BenchmarkValidator:

    def __init__(self):
        self.relevance_agent = RelevanceJudgeAgent()
        self.accuracy_agent = AccuracyJudgeAgent()
        self.hallucination_agent = HallucinationDetectionAgent()

    def validate_relevance_agent(self):

        print("\n" + "=" * 60)
        print("RELEVANCE AGENT VALIDATION")
        print("=" * 60)

        test_cases = [

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

        for i, test in enumerate(test_cases, start=1):

            result = self.relevance_agent.evaluate(
                test["question"],
                test["response"]
            )

            print(f"\nTest Case {i}")
            print(result)

    def validate_accuracy_agent(self):

        print("\n" + "=" * 60)
        print("ACCURACY AGENT VALIDATION")
        print("=" * 60)

        test_cases = [

            {
                "response": "The capital of France is Paris.",
                "reference": "Paris is the capital of France."
            },

            {
                "response": "HTTP is used for communication on the web.",
                "reference": "HTTP is a protocol used for communication on the web."
            },

            {
                "response": "Machine Learning is a subset of AI.",
                "reference": "Machine Learning is a subset of Artificial Intelligence."
            }

        ]

        for i, test in enumerate(test_cases, start=1):

            result = self.accuracy_agent.evaluate(
                test["response"],
                test["reference"]
            )

            print(f"\nTest Case {i}")
            print(result)

    def validate_hallucination_agent(self):

        print("\n" + "=" * 60)
        print("HALLUCINATION AGENT VALIDATION")
        print("=" * 60)

        test_cases = [

            {
                "response": "Paris is the capital of France.",
                "reference": "Paris is the capital of France."
            },

            {
                "response": "Paris is the capital of France. It is located in Germany.",
                "reference": "Paris is the capital of France."
            },

            {
                "response": "Python was created by Guido van Rossum. It won a Nobel Prize.",
                "reference": "Python was created by Guido van Rossum."
            }

        ]

        for i, test in enumerate(test_cases, start=1):

            result = self.hallucination_agent.evaluate(
                test["response"],
                test["reference"]
            )

            print(f"\nTest Case {i}")
            print(result)

    def validate_all(self):

        self.validate_relevance_agent()
        self.validate_accuracy_agent()
        self.validate_hallucination_agent()