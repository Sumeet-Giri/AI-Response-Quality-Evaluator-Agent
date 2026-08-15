from pydantic import BaseModel


class HallucinationResult(BaseModel):
    hallucination_score: int
    supported_claims: list[str]
    hallucinated_claims: list[str]
    total_claims: int
    supported_claims_count: int
    hallucinated_claims_count: int
    hallucination_rate: float
    verifiable: bool = True  # False when no reference/evidence was available -- see hallucination_agent.py
    reasoning: str  