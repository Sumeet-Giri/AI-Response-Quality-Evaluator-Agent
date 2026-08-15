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

    # Optional tagging for evaluation history / the Dashboard (Milestone 4).
    # None of these affect scoring -- they're metadata recorded alongside
    # the result so past evaluations can be grouped and compared later
    # (e.g. "GPT-4" vs "Claude" system_name, or all rows of one CSV batch
    # sharing a batch_id). Fully optional and backward compatible: a
    # request that omits them behaves exactly as before.
    system_name: str = "Unspecified"
    batch_id: str | None = None
    batch_label: str | None = None

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

    @field_validator("system_name")
    @classmethod
    def _normalize_system_name(cls, value: str) -> str:
        value = (value or "").strip()
        return value if value else "Unspecified"
