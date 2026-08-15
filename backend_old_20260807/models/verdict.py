from pydantic import BaseModel


class VerdictResult(BaseModel):
    overall_score: float
    final_verdict: str

    quality_gate_passed: bool
    failed_conditions: list[str]

    weighted_breakdown: dict

    strengths: list[str]
    weaknesses: list[str]

    consolidated_reasoning: str