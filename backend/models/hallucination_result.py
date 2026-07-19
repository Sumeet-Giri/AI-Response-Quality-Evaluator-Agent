from pydantic import BaseModel


class HallucinationResult(BaseModel):
    hallucination_score: int
    supported_claims: list[str]
    hallucinated_claims: list[str]
    reasoning: str