from app.services.embedder import generate_query_embedding
from app.services.similarity import calculate_cosine_similarity

from models.accuracy_result import AccuracyResult


class AccuracyJudgeAgent:

    def get_similarity(self, response: str, reference_answer: str):
        """
        Calculate semantic similarity between
        the AI response and the reference answer.
        """

        response_embedding = generate_query_embedding(response)

        reference_embedding = generate_query_embedding(
            reference_answer
        )

        similarity = calculate_cosine_similarity(
            response_embedding,
            reference_embedding
        )

        return similarity

    def calculate_score(self, similarity: float):
        """
        Calculate accuracy score out of 10.
        """

        if similarity >= 0.85:
            return 10

        elif similarity >= 0.70:
            return 8

        elif similarity >= 0.55:
            return 6

        elif similarity >= 0.40:
            return 4

        elif similarity >= 0.20:
            return 2

        else:
            return 0

    def check_factual_correctness(self, score: int):
        """
        Determine whether the response is factually correct.
        """

        return score >= 6

    def generate_reasoning(self, score: int):

        if score == 10:
            return "The response is factually accurate and matches the reference answer."

        elif score == 8:
            return "The response is mostly accurate with minor differences."

        elif score == 6:
            return "The response is partially accurate."

        elif score == 4:
            return "The response contains limited factual accuracy."

        elif score == 2:
            return "The response is largely inaccurate."

        else:
            return "The response is factually incorrect."

    def evaluate(self, response: str, reference_answer: str):
        """
        Perform complete accuracy evaluation.
        """

        similarity = self.get_similarity(
            response,
            reference_answer
        )

        score = self.calculate_score(
            similarity
        )

        factually_correct = self.check_factual_correctness(
            score
        )

        reasoning = self.generate_reasoning(
            score
        )

        result = AccuracyResult(
            score=score,
            semantic_similarity=round(similarity, 4),
            factually_correct=factually_correct,
            evidence=[reference_answer],
            reasoning=reasoning
        )

        return result