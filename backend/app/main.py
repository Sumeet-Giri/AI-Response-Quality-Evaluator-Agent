from fastapi import FastAPI

from app.api import evaluate
from app.api import validation


app = FastAPI(
    title="AI Response Quality Evaluator Agent"
)


app.include_router(
    evaluate.router,
    prefix="/evaluate",
    tags=["Evaluation"]
)


app.include_router(
    validation.router,
    prefix="/validation",
    tags=["Validation"]
)