from app.schemas.relevance import RelevanceResult
from app.schemas.accuracy import AccuracyResult
from app.schemas.hallucination import HallucinationResult
from app.schemas.completeness import CompletenessResult
from app.schemas.verdict import VerdictResult


class VerdictAgent:

    # ---------------------------------------------------------
    # Weight Configuration
    # ---------------------------------------------------------

    WEIGHTS = {
        "relevance": 0.25,
        "accuracy": 0.35,
        "hallucination": 0.25,
        "completeness": 0.15
    }

    # ---------------------------------------------------------
    # Main Evaluation Method
    # ---------------------------------------------------------

    def evaluate(
        self,
        relevance_result: RelevanceResult,
        accuracy_result: AccuracyResult,
        hallucination_result: HallucinationResult,
        completeness_result: CompletenessResult
    ) -> VerdictResult:

        quality_gate_passed, failed_conditions = \
            self._quality_gate_check(
                relevance_result.score,
                accuracy_result.score,
                hallucination_result.hallucination_score,
                accuracy_result.verifiable,
                hallucination_result.verifiable,
            )

        weighted_breakdown, overall_score = \
            self._calculate_weighted_score(
                relevance_result.score,
                accuracy_result.score,
                hallucination_result.hallucination_score,
                completeness_result.completeness_score
            )

        final_verdict = self._generate_final_verdict(
            overall_score,
            quality_gate_passed
        )

        strengths = self._generate_strengths(
            relevance_result.score,
            accuracy_result.score,
            hallucination_result.hallucination_score,
            completeness_result.completeness_score
        )

        weaknesses = self._generate_weaknesses(
            relevance_result.score,
            accuracy_result.score,
            hallucination_result.hallucination_score,
            completeness_result.completeness_score,
            accuracy_result.verifiable,
            hallucination_result.verifiable,
        )

        consolidated_reasoning = self._generate_reasoning(
            strengths,
            weaknesses,
            final_verdict
        )

        return VerdictResult(
            overall_score=overall_score,
            final_verdict=final_verdict,
            quality_gate_passed=quality_gate_passed,
            failed_conditions=failed_conditions,
            weighted_breakdown=weighted_breakdown,
            strengths=strengths,
            weaknesses=weaknesses,
            consolidated_reasoning=consolidated_reasoning
        )

    # ---------------------------------------------------------
    # Quality Gate Checks
    # ---------------------------------------------------------

    def _quality_gate_check(
        self,
        relevance_score,
        accuracy_score,
        hallucination_score,
        accuracy_verifiable=True,
        hallucination_verifiable=True,
    ):

        failed_conditions = []

        if relevance_score < 4:
            failed_conditions.append(
                "Response is not sufficiently relevant."
            )

        if accuracy_score < 4:
            if accuracy_verifiable:
                failed_conditions.append(
                    "Response is factually inaccurate."
                )
            else:
                failed_conditions.append(
                    "Accuracy could not be verified (no reference answer or "
                    "retrieved evidence was available) -- counted conservatively "
                    "as a gate failure, not as a confirmed inaccuracy."
                )

        if hallucination_score < 4:
            if hallucination_verifiable:
                failed_conditions.append(
                    "Response contains unsupported or hallucinated information."
                )
            else:
                failed_conditions.append(
                    "Hallucination risk could not be assessed (no reference "
                    "answer or retrieved evidence was available) -- counted "
                    "conservatively as a gate failure, not as a confirmed "
                    "hallucination."
                )

        quality_gate_passed = len(failed_conditions) == 0

        return quality_gate_passed, failed_conditions

    # ---------------------------------------------------------
    # Weighted Score Calculation
    # ---------------------------------------------------------

    def _calculate_weighted_score(
        self,
        relevance_score,
        accuracy_score,
        hallucination_score,
        completeness_score
    ):

        weighted_breakdown = {
            "relevance": round(
                relevance_score * self.WEIGHTS["relevance"], 2
            ),
            "accuracy": round(
                accuracy_score * self.WEIGHTS["accuracy"], 2
            ),
            "hallucination": round(
                hallucination_score * self.WEIGHTS["hallucination"], 2
            ),
            "completeness": round(
                completeness_score * self.WEIGHTS["completeness"], 2
            )
        }

        overall_score = round(
            sum(weighted_breakdown.values()),
            2
        )

        return weighted_breakdown, overall_score

    # ---------------------------------------------------------
    # Verdict Classification
    # ---------------------------------------------------------

    def _generate_final_verdict(
        self,
        overall_score,
        quality_gate_passed
    ):

        if not quality_gate_passed:
            return "FAIL"

        if overall_score >= 9:
            return "EXCELLENT"

        elif overall_score >= 8:
            return "GOOD"

        elif overall_score >= 6:
            return "NEEDS IMPROVEMENT"

        else:
            return "POOR"

    # ---------------------------------------------------------
    # Strengths
    # ---------------------------------------------------------

    def _generate_strengths(
        self,
        relevance_score,
        accuracy_score,
        hallucination_score,
        completeness_score
    ):

        strengths = []

        if relevance_score >= 8:
            strengths.append(
                "The response is highly relevant to the question."
            )

        if accuracy_score >= 8:
            strengths.append(
                "The response is factually accurate."
            )

        if hallucination_score >= 8:
            strengths.append(
                "No hallucinated or unsupported claims were detected."
            )

        if completeness_score >= 8:
            strengths.append(
                "The response provides comprehensive coverage."
            )

        return strengths

    # ---------------------------------------------------------
    # Weaknesses
    # ---------------------------------------------------------

    def _generate_weaknesses(
        self,
        relevance_score,
        accuracy_score,
        hallucination_score,
        completeness_score,
        accuracy_verifiable=True,
        hallucination_verifiable=True,
    ):

        weaknesses = []

        if relevance_score < 8:
            weaknesses.append(
                "The response could be more relevant to the question."
            )

        if accuracy_score < 8:
            if accuracy_verifiable:
                weaknesses.append(
                    "The factual correctness of the response could be improved."
                )
            else:
                weaknesses.append(
                    "Accuracy could not be verified -- no reference answer or "
                    "retrieved evidence was available for comparison."
                )

        if hallucination_score < 8:
            if hallucination_verifiable:
                weaknesses.append(
                    "Some claims may lack sufficient factual support."
                )
            else:
                weaknesses.append(
                    "Hallucination risk could not be assessed -- no reference "
                    "answer or retrieved evidence was available for comparison."
                )

        if completeness_score < 8:
            weaknesses.append(
                "The response could provide more comprehensive details."
            )

        return weaknesses

    # ---------------------------------------------------------
    # Consolidated Reasoning
    # ---------------------------------------------------------

    def _generate_reasoning(
        self,
        strengths,
        weaknesses,
        final_verdict
    ):

        reasoning_parts = []

        if strengths:
            reasoning_parts.append(
                "Strengths: " + " ".join(strengths)
            )

        if weaknesses:
            reasoning_parts.append(
                "Weaknesses: " + " ".join(weaknesses)
            )

        reasoning_parts.append(
            f"Final Verdict: {final_verdict}."
        )

        return "\n".join(reasoning_parts)