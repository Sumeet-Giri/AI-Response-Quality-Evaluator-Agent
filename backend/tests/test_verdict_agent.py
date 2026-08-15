"""Real pytest tests for VerdictAgent. Pure math given known inputs --
every assertion here is an exact expected value, not a qualitative check."""

from app.agents.verdict_agent import VerdictAgent
from app.schemas.relevance import RelevanceResult
from app.schemas.accuracy import AccuracyResult
from app.schemas.hallucination import HallucinationResult
from app.schemas.completeness import CompletenessResult

verdict_agent = VerdictAgent()


def _make_results(relevance=10, accuracy=3, hallucination=2, completeness=8):
    return (
        RelevanceResult(score=relevance, semantic_similarity=0.95, topic_match=True, reasoning="."),
        AccuracyResult(score=accuracy, semantic_similarity=0.35, factually_correct=accuracy >= 6, evidence=[], reasoning="."),
        HallucinationResult(hallucination_score=hallucination, supported_claims=[], hallucinated_claims=[],
                             total_claims=0, supported_claims_count=0, hallucinated_claims_count=0,
                             hallucination_rate=0.0, reasoning="."),
        CompletenessResult(completeness_score=completeness, coverage_percentage=80.0, total_aspects=5,
                            extracted_aspects=[], covered_aspects=[], missing_aspects=[], reasoning="."),
    )


def test_weighted_score_matches_hand_calculation():
    relevance, accuracy, hallucination, completeness = _make_results(
        relevance=10, accuracy=3, hallucination=2, completeness=8
    )
    result = verdict_agent.evaluate(relevance, accuracy, hallucination, completeness)

    # 10*0.25 + 3*0.35 + 2*0.25 + 8*0.15 = 2.5 + 1.05 + 0.5 + 1.2 = 5.25
    assert result.weighted_breakdown == {
        "relevance": 2.5,
        "accuracy": 1.05,
        "hallucination": 0.5,
        "completeness": 1.2,
    }
    assert result.overall_score == 5.25


def test_quality_gate_fails_below_threshold_even_with_ok_overall_score():
    # accuracy=3 and hallucination=2 are both < 4 -> hard fail,
    # regardless of the weighted overall score.
    relevance, accuracy, hallucination, completeness = _make_results(
        relevance=10, accuracy=3, hallucination=2, completeness=8
    )
    result = verdict_agent.evaluate(relevance, accuracy, hallucination, completeness)

    assert result.quality_gate_passed is False
    assert result.final_verdict == "FAIL"
    assert len(result.failed_conditions) == 2  # accuracy AND hallucination both failed


def test_quality_gate_passes_and_verdict_label_matches_score_band():
    relevance, accuracy, hallucination, completeness = _make_results(
        relevance=10, accuracy=10, hallucination=10, completeness=10
    )
    result = verdict_agent.evaluate(relevance, accuracy, hallucination, completeness)

    assert result.quality_gate_passed is True
    assert result.overall_score == 10.0
    assert result.final_verdict == "EXCELLENT"


def test_weights_sum_to_one():
    assert sum(VerdictAgent.WEIGHTS.values()) == 1.0


def test_completeness_alone_cannot_trigger_the_quality_gate():
    # Completeness has no gate condition by design -- a very low
    # completeness score with everything else strong should still pass.
    relevance, accuracy, hallucination, completeness = _make_results(
        relevance=10, accuracy=10, hallucination=10, completeness=0
    )
    result = verdict_agent.evaluate(relevance, accuracy, hallucination, completeness)
    assert result.quality_gate_passed is True


def test_unverifiable_accuracy_and_hallucination_do_not_produce_false_weaknesses():
    # Regression test for the exact issue found in a real PDF report:
    # "The factual correctness of the response could be improved" and
    # "Some claims may lack sufficient factual support" appeared even
    # though the per-dimension reasoning correctly said "could not be
    # verified" -- the verdict layer was independently re-deriving
    # misleading text purely from the numeric score, blind to *why* it
    # was low.
    relevance, accuracy, hallucination, completeness = _make_results(
        relevance=6, accuracy=0, hallucination=0, completeness=10
    )
    accuracy = accuracy.model_copy(update={"verifiable": False})
    hallucination = hallucination.model_copy(update={"verifiable": False})

    result = verdict_agent.evaluate(relevance, accuracy, hallucination, completeness)

    assert not any("factual correctness of the response could be improved" in w for w in result.weaknesses)
    assert not any("claims may lack sufficient factual support" in w for w in result.weaknesses)
    assert any("could not be verified" in w.lower() for w in result.weaknesses)
    assert any("could not be assessed" in w.lower() for w in result.weaknesses)

    # Gate behavior is unchanged -- still conservatively fails.
    assert result.quality_gate_passed is False
    assert not any("factually inaccurate" in c for c in result.failed_conditions)
    assert not any("contains unsupported or hallucinated" in c for c in result.failed_conditions)
    assert any("could not be verified" in c.lower() for c in result.failed_conditions)


def test_verifiable_defaults_to_true_for_backward_compatibility():
    # Existing callers that construct results without specifying
    # `verifiable` (e.g. older test fixtures) must keep the original
    # (pre-fix) weakness/failed_condition wording.
    relevance, accuracy, hallucination, completeness = _make_results(
        relevance=6, accuracy=0, hallucination=0, completeness=10
    )
    result = verdict_agent.evaluate(relevance, accuracy, hallucination, completeness)
    assert any("factual correctness of the response could be improved" in w for w in result.weaknesses)
    assert any("claims may lack sufficient factual support" in w for w in result.weaknesses)
