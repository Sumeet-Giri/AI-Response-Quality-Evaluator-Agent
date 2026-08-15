from pydantic import BaseModel, field_validator


class EvaluationRequest(BaseModel):
    """
    Input contract for every /evaluate/* endpoint.

    question / response are required and must contain non-whitespace
    content. This closes a real gap found during architecture review:
    previously an empty string passed straight through the entire agent
    pipeline and produced a "valid" (if low) score instead of a clean
    validation error.

    reference_answer is optional. When omitted (or blank),
    EvaluationOrchestrator falls back to retrieving the closest passage
    from the reference knowledge base (RAG) instead of leaving Accuracy /
    Hallucination scoring with nothing to compare against.
    """

    question: str
    response: str
    reference_answer: str = ""

    @field_validator("question", "response")
    @classmethod
    def _must_not_be_blank(cls, value: str, info):
        if value is None or not value.strip():
            raise ValueError(f"'{info.field_name}' cannot be empty or whitespace-only.")
        return value.strip()

    @field_validator("reference_answer")
    @classmethod
    def _normalize_reference(cls, value: str) -> str:
        return (value or "").strip()
