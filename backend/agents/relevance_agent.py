from app.services.embedder import generate_query_embedding
from app.services.similarity import calculate_cosine_similarity

from models.relevance_result import RelevanceResult


class RelevanceJudgeAgent:

    def get_similarity(self, question: str, response: str):
        """
        Generate embeddings for the question and response
        and calculate their cosine similarity.
        """
        question_embedding = generate_query_embedding(question)
        response_embedding = generate_query_embedding(response)

        similarity = calculate_cosine_similarity(
            question_embedding,
            response_embedding
        )

        return similarity

    def check_topic_match(self, similarity: float):
        """
        Check whether the response matches the topic of the question.
        """

        # This threshold can be tuned later if needed.
        return similarity >= 0.50

    def calculate_score(self, similarity: float, topic_match: bool):
        """
        Calculate relevance score (out of 10).
        """

        # If the topic does not match, assign 0.
        if not topic_match:
            return 0

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

    def generate_reasoning(self, score: int, topic_match: bool):
        """
        Generate reasoning for the assigned score.
        """

        if not topic_match:
            return "The response does not address the intended topic of the question."

        if score == 10:
            return "The response is highly relevant and directly answers the question."

        elif score == 8:
            return "The response is relevant but could provide more details."

        elif score == 6:
            return "The response is moderately relevant and partially answers the question."

        elif score == 4:
            return "The response has limited relevance to the question."

        elif score == 2:
            return "The response is mostly irrelevant."

        else:
            return "The response is completely unrelated to the question."

    def evaluate(self, question: str, response: str):
        """
        Perform complete relevance evaluation.
        """

        similarity = self.get_similarity(
            question,
            response
        )

        topic_match = self.check_topic_match(
            similarity
        )

        score = self.calculate_score(
            similarity,
            topic_match
        )

        reasoning = self.generate_reasoning(
            score,
            topic_match
        )

        result = RelevanceResult(
            score=score,
            semantic_similarity=round(similarity, 4),
            topic_match=topic_match,
            reasoning=reasoning
        )

        return result