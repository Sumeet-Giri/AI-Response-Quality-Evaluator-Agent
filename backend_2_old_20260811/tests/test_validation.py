"""Real pytest test for BenchmarkValidator (previously: a script that
just printed validate_all() with no assertions)."""

from app.validation.validator import BenchmarkValidator
from app.validation.benchmark_cases import (
    RELEVANCE_TEST_CASES,
    ACCURACY_TEST_CASES,
    HALLUCINATION_TEST_CASES,
    COMPLETENESS_TEST_CASES,
)

validator = BenchmarkValidator()


def test_validate_all_covers_every_agent_with_scoring_logic():
    results = validator.validate_all()

    expected_keys = {
        "relevance_validation",
        "accuracy_validation",
        "hallucination_validation",
        "completeness_validation",
    }
    assert set(results.keys()) == expected_keys

    assert len(results["relevance_validation"]) == len(RELEVANCE_TEST_CASES)
    assert len(results["accuracy_validation"]) == len(ACCURACY_TEST_CASES)
    assert len(results["hallucination_validation"]) == len(HALLUCINATION_TEST_CASES)
    assert len(results["completeness_validation"]) == len(COMPLETENESS_TEST_CASES)

    # Every result entry must carry a "result" payload with a numeric score field.
    for entry in results["relevance_validation"]:
        assert "score" in entry["result"]
