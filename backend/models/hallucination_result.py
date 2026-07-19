from typing import List

class HallucinationResult:

    score: float

    reasoning: str

    supported_claims: List[str]

    hallucinated_claims: List[str]

    supported_percentage: float