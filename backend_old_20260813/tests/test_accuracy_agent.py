"""Real pytest tests for AccuracyJudgeAgent. Same relative-comparison
principle as test_relevance_agent.py -- see that file's docstring."""

import pytest
from app.agents.accuracy_agent import AccuracyJudgeAgent

agent = AccuracyJudgeAgent()


def test_matching_response_scores_higher_than_wrong_one():
    reference = "Paris is the capital of France."
    matching = agent.evaluate("The capital of France is Paris.", reference)
    wrong = agent.evaluate("I like watching cricket on weekends.", reference)

    assert 0 <= matching.score <= 10
    assert 0 <= wrong.score <= 10
    assert matching.score > wrong.score


def test_factually_correct_flag_matches_score_threshold():
    # check_factual_correctness is a pure function of score -- verify the
    # >=6 cutoff directly, independent of the embedding model.
    assert agent.check_factual_correctness(score=6) is True
    assert agent.check_factual_correctness(score=5) is False


def test_evidence_field_carries_the_reference_answer():
    reference = "Paris is the capital of France."
    result = agent.evaluate("The capital of France is Paris.", reference)
    assert result.evidence == [reference]


def test_score_buckets_are_exact():
    assert agent.calculate_score(0.90) == 10
    assert agent.calculate_score(0.10) == 0
