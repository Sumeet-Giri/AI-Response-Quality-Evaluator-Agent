from app.models.schemas import EvaluationRequest


def validate_input(request: EvaluationRequest):
    """
    Perform additional validation on the evaluation request.
    """

    if not request.question.strip():
        raise ValueError("Question cannot be empty.")

    if not request.ai_response.strip():
        raise ValueError("AI response cannot be empty.")

    return True