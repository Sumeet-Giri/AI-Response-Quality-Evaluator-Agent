from fastapi import APIRouter

from validation.validator import BenchmarkValidator


router = APIRouter()

@router.get("/relevance")
def validate_relevance():

    validator = BenchmarkValidator()

    return validator.validate_relevance_agent()

@router.get("/accuracy")
def validate_accuracy():

    validator = BenchmarkValidator()

    return validator.validate_accuracy_agent()

@router.get("/hallucination")
def validate_hallucination():

    validator = BenchmarkValidator()

    return validator.validate_hallucination_agent()

@router.get("/all")
def validate_all():

    validator = BenchmarkValidator()

    return validator.validate_all()