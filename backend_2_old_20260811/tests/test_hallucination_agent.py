"""Real pytest tests for HallucinationDetectionAgent."""

from app.agents.hallucination_agent import HallucinationDetectionAgent

agent = HallucinationDetectionAgent()


def test_fully_supported_response_scores_higher_than_padded_one():
    reference = "Paris is the capital of France."
    supported_only = agent.evaluate("Paris is the capital of France.", reference)
    with_extra_claim = agent.evaluate(
        "Paris is the capital of France. I like watching cricket on weekends.",
        reference,
    )
    assert supported_only.hallucination_score >= with_extra_claim.hallucination_score
    assert supported_only.hallucinated_claims == []
    assert len(with_extra_claim.hallucinated_claims) >= 1


def test_extract_claims_splits_on_sentence_boundaries():
    claims = agent.extract_claims("Claim one. Claim two. Claim three.")
    assert claims == ["Claim one", "Claim two", "Claim three"]


def test_extract_claims_ignores_empty_fragments():
    claims = agent.extract_claims("Only one claim.")
    assert claims == ["Only one claim"]


def test_score_is_zero_when_there_are_no_claims():
    assert agent.calculate_score(supported_claims=[], hallucinated_claims=[]) == 0


def test_score_is_ratio_of_supported_to_total():
    # Pure function, independent of the embedding model -- exact value.
    score = agent.calculate_score(
        supported_claims=["a", "b", "c"],
        hallucinated_claims=["d"],
    )
    assert score == int((3 / 4) * 10)
