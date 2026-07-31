from pydantic import BaseModel


class AccuracyResult(BaseModel):
    score: int
    semantic_similarity: float
    factually_correct: bool
    evidence: list[str]
    reasoning: str