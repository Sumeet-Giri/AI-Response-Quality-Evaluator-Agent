"""Real pytest tests (previously: a print-and-eyeball script with zero
assertions). Score assertions are RELATIVE (on-topic vs. off-topic)
rather than absolute thresholds, deliberately: the exact numeric score
for a given pair of sentences depends on the embedding model, and this
suite runs against a lightweight deterministic fake embedding (see
conftest.py) rather than downloading real model weights. What must hold
true under *any* reasonable embedding is that a response sharing the
question's subject scores higher than one that doesn't -- that's what's
asserted here. The pure bucketing/gating logic (independent of any
embedding) is asserted exactly."""

import pytest
from app.agents.relevance_agent import RelevanceJudgeAgent

agent = RelevanceJudgeAgent()

RELATED_PAIRS = [
    ("What is the capital of France?", "The capital of France is Paris."),
    ("What is HTTP?", "HTTP is a protocol used for communication on the web."),
    ("Explain the water cycle.", "The water cycle describes how water evaporates and falls as rain."),
]

UNRELATED_RESPONSE = "I like watching cricket on weekends."


@pytest.mark.parametrize("question,related_response", RELATED_PAIRS)
def test_related_response_is_more_similar_than_unrelated(question, related_response):
    related = agent.evaluate(question, related_response)
    unrelated = agent.evaluate(question, UNRELATED_RESPONSE)

    assert 0 <= related.score <= 10
    assert 0 <= unrelated.score <= 10
    # Compare the continuous semantic_similarity, not the gated score: the
    # topic_match gate can legitimately tie two different similarities at
    # score=0 if both happen to fall under the 0.50 threshold, so score
    # isn't the right field to assert a strict ordering on -- similarity
    # is the underlying signal this test actually cares about.
    assert related.semantic_similarity > unrelated.semantic_similarity, (
        f"expected a topically-related response to be more semantically "
        f"similar than an unrelated one ({related.semantic_similarity} "
        f"vs {unrelated.semantic_similarity})"
    )


def test_topic_match_gate_forces_zero_when_false():
    # calculate_score is a pure function of (similarity, topic_match) --
    # verify the hard gate directly, independent of the embedding model.
    assert agent.calculate_score(similarity=0.99, topic_match=False) == 0


def test_topic_match_threshold_is_exact():
    assert agent.check_topic_match(0.50) is True
    assert agent.check_topic_match(0.49) is False


def test_score_buckets_are_monotonic_in_similarity():
    similarities = [0.95, 0.80, 0.60, 0.45, 0.25, 0.05]
    scores = [agent.calculate_score(s, topic_match=True) for s in similarities]
    assert scores == sorted(scores, reverse=True), (
        "higher similarity must never produce a lower score"
    )


def test_score_buckets_are_exact():
    assert agent.calculate_score(0.90, topic_match=True) == 10
    assert agent.calculate_score(0.75, topic_match=True) == 8
    assert agent.calculate_score(0.60, topic_match=True) == 6
    assert agent.calculate_score(0.45, topic_match=True) == 4
    assert agent.calculate_score(0.25, topic_match=True) == 2
    assert agent.calculate_score(0.10, topic_match=True) == 0
