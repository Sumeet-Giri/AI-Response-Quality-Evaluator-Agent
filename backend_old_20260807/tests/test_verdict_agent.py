from agents.verdict_agent import VerdictAgent

from models.relevance import RelevanceResult
from models.accuracy import AccuracyResult
from models.hallucination import HallucinationResult
from models.completeness import CompletenessResult


def test_verdict_agent():

    relevance = RelevanceResult(
        score=10,
        semantic_similarity=0.95,
        topic_match=True,
        reasoning="Highly relevant."
    )

    accuracy = AccuracyResult(
    score=3,
    semantic_similarity=0.35,
    factually_correct=False,
    evidence=[],
    reasoning="Incorrect."
)

    hallucination = HallucinationResult(
    hallucination_score=2,
    supported_claims=[],
    hallucinated_claims=["Incorrect claim"],
    reasoning="Hallucinations detected."
)

    completeness = CompletenessResult(
        completeness_score=8,
        coverage_percentage=80.0,
        total_aspects=5,
        extracted_aspects=[],
        covered_aspects=[],
        missing_aspects=[],
        reasoning="Mostly complete."
    )

    verdict_agent = VerdictAgent()

    result = verdict_agent.evaluate(
        relevance,
        accuracy,
        hallucination,
        completeness
    )

    print(result.model_dump())


if __name__ == "__main__":
    test_verdict_agent()