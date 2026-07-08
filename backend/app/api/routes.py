from fastapi import APIRouter, HTTPException  # type: ignore[import]

from app.models.schemas import EvaluationRequest
from app.services.input_validator import validate_input

router = APIRouter()


@router.post("/evaluate")
async def evaluate(request: EvaluationRequest):
    """
    Accepts an evaluation request and validates the input.
    """

    try:
        validate_input(request)

        return {
            "status": "success",
            "message": "Input validated successfully.",
            "data": request.model_dump()
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )