from agents.relevance_agent import RelevanceJudgeAgent
from agents.accuracy_agent import AccuracyJudgeAgent
from agents.hallucination_agent import HallucinationDetectionAgent

from validation.benchmark_cases import (
    RELEVANCE_TEST_CASES,
    ACCURACY_TEST_CASES,
    HALLUCINATION_TEST_CASES
)


class BenchmarkValidator:

    # ----------------------------------
    # RELEVANCE VALIDATION
    # ----------------------------------

    def validate_relevance_agent(self):

        agent = RelevanceJudgeAgent()
        results = []

        for case in RELEVANCE_TEST_CASES:

            result = agent.evaluate(
                case["question"],
                case["response"]
            )

            results.append({
                "question": case["question"],
                "response": case["response"],
                "result": result.model_dump()
            })

        return results

    # ----------------------------------
    # ACCURACY VALIDATION
    # ----------------------------------

    def validate_accuracy_agent(self):

        agent = AccuracyJudgeAgent()
        results = []

        for case in ACCURACY_TEST_CASES:

            result = agent.evaluate(
                case["response"],
                case["reference_answer"]
            )

            results.append({
                "response": case["response"],
                "reference_answer": case["reference_answer"],
                "result": result.model_dump()
            })

        return results

    # ----------------------------------
    # HALLUCINATION VALIDATION
    # ----------------------------------

    def validate_hallucination_agent(self):

        agent = HallucinationDetectionAgent()
        results = []

        for case in HALLUCINATION_TEST_CASES:

            result = agent.evaluate(
                case["response"],
                case["reference_answer"]
            )

            results.append({
                "response": case["response"],
                "reference_answer": case["reference_answer"],
                "result": result.model_dump()
            })

        return results

    # ----------------------------------
    # VALIDATE ALL
    # ----------------------------------

    def validate_all(self):

        return {
            "relevance_validation":
            self.validate_relevance_agent(),

            "accuracy_validation":
            self.validate_accuracy_agent(),

            "hallucination_validation":
            self.validate_hallucination_agent()
        }