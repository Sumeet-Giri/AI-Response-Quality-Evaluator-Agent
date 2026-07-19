from app.services.embedder import generate_query_embedding
from app.services.similarity import calculate_cosine_similarity

from models.hallucination_result import HallucinationResult


class HallucinationDetectionAgent:

    def extract_claims(self, response: str):
        """
        Split the response into individual factual claims.
        """

        claims = [
            claim.strip()
            for claim in response.split(".")
            if claim.strip()
        ]

        return claims

    def verify_claims(self, claims, reference_answer):
        """
        Check whether each claim is supported by the reference answer.
        """

        supported_claims = []
        hallucinated_claims = []

        # Generate embedding for the reference answer once
        reference_embedding = generate_query_embedding(
            reference_answer
        )

        for claim in claims:

            # Generate embedding for the current claim
            claim_embedding = generate_query_embedding(
                claim
            )

            # Calculate similarity
            similarity = calculate_cosine_similarity(
                claim_embedding,
                reference_embedding
            )

            # Threshold for considering a claim as supported
            if similarity >= 0.60:
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
        Calculate hallucination score out of 10.
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

    def generate_reasoning(self, score: int):
        """
        Generate reasoning based on hallucination score.
        """

        if score == 10:
            return "No hallucinations were detected."

        elif score >= 7:
            return "The response contains minor unsupported claims."

        elif score >= 4:
            return "The response contains some hallucinated information."

        else:
            return "The response contains significant hallucinations."

    def evaluate(
        self,
        response: str,
        reference_answer: str
    ):
        """
        Perform complete hallucination detection.
        """

        # Extract factual claims
        claims = self.extract_claims(
            response
        )

        # Verify claims
        supported_claims, hallucinated_claims = (
            self.verify_claims(
                claims,
                reference_answer
            )
        )

        # Calculate score
        score = self.calculate_score(
            supported_claims,
            hallucinated_claims
        )

        # Generate reasoning
        reasoning = self.generate_reasoning(
            score
        )

        # Prepare final result
        result = HallucinationResult(
            hallucination_score=score,
            supported_claims=supported_claims,
            hallucinated_claims=hallucinated_claims,
            reasoning=reasoning
        )

        return result