from app.services.embedder import generate_query_embedding
from app.services.similarity import calculate_cosine_similarity

from app.schemas.hallucination import HallucinationResult


class HallucinationDetectionAgent:

    CLAIM_SIMILARITY_THRESHOLD = 0.60

    NOT_VERIFIABLE_REASONING = (
        "Hallucination could not be assessed: no reference answer or "
        "retrieved evidence was available for comparison. This is NOT a "
        "determination that the response contains hallucinations -- there "
        "was simply nothing to check its claims against."
    )

    def extract_claims(self, response: str):
        """
        Split the response into individual factual claims.

        Each sentence is treated as one claim for the current
        rule-based claim extraction approach.
        """

        claims = [
            claim.strip()
            for claim in response.split(".")
            if claim.strip()
        ]

        return claims

    def verify_claims(self, claims, reference_answer):
        """
        Check whether each response claim is supported by the
        reference answer.

        Instead of comparing a response claim with the entire
        reference answer, the reference is first divided into
        individual claims.

        Each response claim is compared against every reference
        claim, and only its best similarity score is used.

        This prevents one highly similar statement in the reference
        from incorrectly supporting an unrelated claim.
        """

        supported_claims = []
        hallucinated_claims = []

        # Extract individual claims from the reference.
        reference_claims = self.extract_claims(
            reference_answer
        )

        # If there is no reference evidence, no claim can be verified
        # either way -- leave both lists empty rather than marking every
        # claim "hallucinated". A claim with nothing to compare it
        # against hasn't been checked, so it can't honestly be reported
        # as unsupported (evaluate() already short-circuits before
        # reaching this method when there's no reference at all; this
        # fallback exists so verify_claims() is also safe to call
        # directly, e.g. from a test, without the same mislabeling risk).
        if not reference_claims:

            return supported_claims, hallucinated_claims

        # Generate embeddings for reference claims once.
        reference_embeddings = [
            generate_query_embedding(reference_claim)
            for reference_claim in reference_claims
        ]

        for claim in claims:

            # Generate embedding for the current response claim.
            claim_embedding = generate_query_embedding(
                claim
            )

            # Find the best matching reference claim.
            best_similarity = 0.0

            for reference_embedding in reference_embeddings:

                similarity = calculate_cosine_similarity(
                    claim_embedding,
                    reference_embedding
                )

                if similarity > best_similarity:
                    best_similarity = similarity

            # A response claim is supported only if its best
            # matching reference claim reaches the threshold.
            if best_similarity >= self.CLAIM_SIMILARITY_THRESHOLD:
                supported_claims.append(claim)

            else:
                hallucinated_claims.append(claim)

        return supported_claims, hallucinated_claims

    def calculate_score(
        self,
        supported_claims,
        hallucinated_claims
    ):
        """
        Calculate hallucination-free score out of 10.

        10 = all claims are supported.
        0 = no claims are supported.
        """

        total_claims = (
            len(supported_claims)
            + len(hallucinated_claims)
        )

        if total_claims == 0:
            return 0

        score = int(
            (len(supported_claims) / total_claims) * 10
        )

        return score

    def calculate_hallucination_metrics(
        self,
        supported_claims,
        hallucinated_claims
    ):
        """
        Calculate claim-level hallucination metrics.
        """

        supported_claims_count = len(
            supported_claims
        )

        hallucinated_claims_count = len(
            hallucinated_claims
        )

        total_claims = (
            supported_claims_count
            + hallucinated_claims_count
        )

        if total_claims == 0:

            hallucination_rate = 0.0

        else:

            hallucination_rate = (
                hallucinated_claims_count
                / total_claims
            ) * 100

        return (
            total_claims,
            supported_claims_count,
            hallucinated_claims_count,
            hallucination_rate
        )

    def generate_reasoning(
        self,
        score: int
    ):
        """
        Generate reasoning based on hallucination score.
        """

        if score == 10:

            return "No hallucinations were detected."

        elif score >= 7:

            return (
                "The response contains minor unsupported claims."
            )

        elif score >= 4:

            return (
                "The response contains some hallucinated information."
            )

        else:

            return (
                "The response contains significant hallucinations."
            )

    def evaluate(
        self,
        response: str,
        reference_answer: str
    ):
        """
        Perform complete hallucination detection.

        When no reference_answer is available, this short-circuits before
        any claim extraction/embedding work: there is nothing to check
        response claims against, so no claim can honestly be labeled
        "hallucinated". Previously, this case fell through to
        verify_claims() with an empty/blank reference, which either
        embedded an empty string as "the reference" (comparing every real
        claim to nothing) or, in an earlier revision, dumped every claim
        straight into hallucinated_claims -- both produced the same
        misleading result: a true statement like "New Delhi is the
        capital of India" being reported as a hallucinated claim purely
        because there was nothing to verify it against, not because
        anything false was detected. Score stays 0 (the same value this
        already produced via the "zero claims" path), so the weighted
        verdict and quality gate behave identically -- only the claim
        lists and reasoning change, to honestly report "not checked"
        instead of falsely reporting "checked and found unsupported".
        """

        has_reference = bool(reference_answer and reference_answer.strip())

        if not has_reference:
            return HallucinationResult(
                hallucination_score=0,
                supported_claims=[],
                hallucinated_claims=[],
                total_claims=0,
                supported_claims_count=0,
                hallucinated_claims_count=0,
                hallucination_rate=0.0,
                verifiable=False,
                reasoning=self.NOT_VERIFIABLE_REASONING,
            )

        # ----------------------------------------------------------
        # Step 1: Extract response claims
        # ----------------------------------------------------------

        claims = self.extract_claims(
            response
        )

        # ----------------------------------------------------------
        # Step 2: Verify claims against reference claims
        # ----------------------------------------------------------

        (
            supported_claims,
            hallucinated_claims
        ) = self.verify_claims(
            claims,
            reference_answer
        )

        # ----------------------------------------------------------
        # Step 3: Calculate hallucination-free score
        # ----------------------------------------------------------

        score = self.calculate_score(
            supported_claims,
            hallucinated_claims
        )

        # ----------------------------------------------------------
        # Step 4: Calculate claim-level metrics
        # ----------------------------------------------------------

        (
            total_claims,
            supported_claims_count,
            hallucinated_claims_count,
            hallucination_rate
        ) = self.calculate_hallucination_metrics(
            supported_claims,
            hallucinated_claims
        )

        # ----------------------------------------------------------
        # Step 5: Generate reasoning
        # ----------------------------------------------------------

        reasoning = self.generate_reasoning(
            score
        )

        # ----------------------------------------------------------
        # Step 6: Build final result
        # ----------------------------------------------------------

        result = HallucinationResult(
            hallucination_score=score,
            supported_claims=supported_claims,
            hallucinated_claims=hallucinated_claims,

            total_claims=total_claims,
            supported_claims_count=supported_claims_count,
            hallucinated_claims_count=hallucinated_claims_count,
            hallucination_rate=hallucination_rate,

            reasoning=reasoning
        )

        return result