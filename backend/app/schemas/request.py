from pydantic import BaseModel


class EvaluationRequest(BaseModel):
    question: str
    response: str
    reference_answer: str = ""