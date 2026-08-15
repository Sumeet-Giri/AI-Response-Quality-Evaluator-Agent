from pathlib import Path
import shutil

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException
)

from app.models.schemas import EvaluationRequest
from app.services.input_validator import (
    validate_input,
    validate_file
)

from app.core.config import UPLOAD_DIR

router = APIRouter()


@router.post("/evaluate")
async def evaluate(

    question: str = Form(...),

    ai_response: str = Form(...),

    reference_answer: str = Form(None),

    source_document: UploadFile = File(None)

):

    request = EvaluationRequest(
        question=question,
        ai_response=ai_response,
        reference_answer=reference_answer
    )

    try:

        validate_input(request)

        uploaded_filename = None

        if source_document:

            validate_file(source_document.filename)

            file_path = UPLOAD_DIR / source_document.filename

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(
                    source_document.file,
                    buffer
                )

            uploaded_filename = source_document.filename

        return {

            "status": "success",

            "message": "Input validated successfully.",

            "uploaded_file": uploaded_filename,

            "data": request.model_dump()

        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )