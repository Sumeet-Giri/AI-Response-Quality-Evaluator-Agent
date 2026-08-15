from pydantic import BaseModel
from typing import List


class CompletenessResult(BaseModel):
    completeness_score: int
    coverage_percentage: float
    total_aspects: int

    extracted_aspects: List[str]
    covered_aspects: List[str]
    missing_aspects: List[str]

    reasoning: str