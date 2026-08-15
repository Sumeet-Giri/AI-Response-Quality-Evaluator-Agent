"""Real pytest tests for CompletenessJudge. This agent is pure
keyword/rule logic with no embedding model, so assertions here can be
exact rather than qualitative."""

from app.agents.completeness_agent import CompletenessJudge

agent = CompletenessJudge()


def test_complete_response_scores_higher_than_partial():
    question = "What is Machine Learning? Explain its types and applications."

    complete = agent.evaluate(
        question=question,
        response=(
            "Machine Learning is a branch of Artificial Intelligence. "
            "It includes supervised, unsupervised and reinforcement learning. "
            "It is used in healthcare, recommendation systems and self-driving cars."
        ),
    )
    definition_only = agent.evaluate(
        question=question,
        response="Machine Learning is a subset of Artificial Intelligence.",
    )

    assert complete.completeness_score > definition_only.completeness_score
    assert complete.coverage_percentage > definition_only.coverage_percentage


def test_empty_response_scores_zero():
    result = agent.evaluate(
        question="Explain Artificial Intelligence.",
        response="",
    )
    assert result.completeness_score == 0
    assert result.coverage_percentage == 0.0
    assert result.covered_aspects == []


def test_extract_aspects_definition_question():
    aspects = agent.extract_aspects("What is Machine Learning?")
    assert "Definition" in aspects


def test_extract_aspects_compare_question():
    aspects = agent.extract_aspects("Compare TCP and UDP.")
    assert "Comparison" in aspects


def test_extract_aspects_falls_back_to_explanation():
    aspects = agent.extract_aspects("Tell me about DNS.")
    assert aspects == ["Explanation"]


def test_coverage_calculation_is_exact():
    assert agent.calculate_coverage(covered=2, total=4) == 50.0
    assert agent.calculate_coverage(covered=0, total=0) == 0.0


def test_score_buckets_are_exact():
    assert agent.calculate_score(coverage=95) == 10
    assert agent.calculate_score(coverage=85) == 9
    assert agent.calculate_score(coverage=0) == 0
    assert agent.calculate_score(coverage=5) == 1
