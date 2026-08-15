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


def test_no_reference_never_labels_a_claim_as_hallucinated():
    # Regression test for the exact reported bug: "New Delhi is the
    # capital of India" (a TRUE statement) was being reported as a
    # hallucinated claim purely because no reference was supplied, not
    # because anything false was detected.
    result = agent.evaluate("New Delhi is the capital of India.", "")
    assert result.hallucinated_claims == []
    assert result.supported_claims == []
    assert result.hallucination_score == 0
    assert result.total_claims == 0
    assert "could not be assessed" in result.reasoning.lower()
    assert "significant hallucinations" not in result.reasoning
    assert "contains significant hallucinations" not in result.reasoning


def test_no_reference_reasoning_does_not_claim_hallucinations_were_found():
    # The old score-banded reasoning ("The response contains significant
    # hallucinations") must not appear when nothing was actually checked.
    result = agent.evaluate("Some response with a claim.", "   ")  # whitespace-only
    assert "significant hallucinations" not in result.reasoning
    assert "could not be assessed" in result.reasoning.lower()


def test_verify_claims_no_reference_fallback_does_not_mislabel():
    # Defense-in-depth: verify_claims() itself must not dump claims into
    # hallucinated_claims when called directly with no reference, even
    # outside of evaluate()'s short-circuit.
    supported, hallucinated = agent.verify_claims(["A true claim"], "")
    assert supported == []
    assert hallucinated == []


def test_claim_matches_best_reference_claim_not_whole_reference():
    # The reference is split into claims and each response claim is
    # matched against its single best-matching reference claim, so a
    # true claim isn't penalized just because OTHER sentences in a
    # multi-topic reference are unrelated to it.
    reference = (
        "The Eiffel Tower is located in Paris. "
        "Mount Everest is the tallest mountain in the world."
    )
    result = agent.evaluate("The Eiffel Tower is located in Paris.", reference)
    assert result.supported_claims == ["The Eiffel Tower is located in Paris"]
    assert result.hallucinated_claims == []
