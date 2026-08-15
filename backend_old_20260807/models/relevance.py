from pydantic import BaseModel


class RelevanceResult(BaseModel):
    score: int
    semantic_similarity: float
    topic_match: bool
    reasoning: str