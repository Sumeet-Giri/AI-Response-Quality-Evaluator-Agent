from app.agents.relevance_agent import RelevanceJudgeAgent
from app.agents.accuracy_agent import AccuracyJudgeAgent
from app.agents.hallucination_agent import HallucinationDetectionAgent
from app.agents.completeness_agent import CompletenessJudge

from app.validation.benchmark_cases import (
    RELEVANCE_TEST_CASES,
    ACCURACY_TEST_CASES,
    HALLUCINATION_TEST_CASES,
    COMPLETENESS_TEST_CASES
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
    # COMPLETENESS VALIDATION
    # ----------------------------------

    def validate_completeness_agent(self):

        agent = CompletenessJudge()
        results = []

        for case in COMPLETENESS_TEST_CASES:

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
    # VALIDATE ALL
    # ----------------------------------

    def validate_all(self):

        return {
            "relevance_validation":
            self.validate_relevance_agent(),

            "accuracy_validation":
            self.validate_accuracy_agent(),

            "hallucination_validation":
            self.validate_hallucination_agent(),

            "completeness_validation":
            self.validate_completeness_agent()
        }