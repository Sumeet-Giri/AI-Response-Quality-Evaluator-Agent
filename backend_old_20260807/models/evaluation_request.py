from typing import List, Optional


class EvaluationRequest:

    question: str

    ai_response: str

    reference_answer: Optional[str]

    retrieved_chunks: Optional[List[str]]