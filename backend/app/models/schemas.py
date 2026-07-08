from typing import Optional
from pydantic import BaseModel, Field # type: ignore


class EvaluationRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=5,
        description="User's question"
    )

    ai_response: str = Field(
        ...,
        min_length=5,
        description="AI-generated response"
    )

    reference_answer: Optional[str] = Field(
        default=None,
        description="Optional reference answer"
    )