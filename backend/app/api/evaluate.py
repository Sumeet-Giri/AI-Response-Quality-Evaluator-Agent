from fastapi import APIRouter

from app.schemas.request import EvaluationRequest

from agents.relevance_agent import RelevanceJudgeAgent
from agents.accuracy_agent import AccuracyJudgeAgent
from agents.hallucination_agent import HallucinationDetectionAgent


router = APIRouter()

@router.post("/relevance")
def evaluate_relevance(data: EvaluationRequest):

    agent = RelevanceJudgeAgent()

    result = agent.evaluate(
        data.question,
        data.response
    )

    return result

@router.post("/accuracy")
def evaluate_accuracy(data: EvaluationRequest):

    agent = AccuracyJudgeAgent()

    result = agent.evaluate(
        data.response,
        data.reference_answer
    )

    return result

@router.post("/hallucination")
def evaluate_hallucination(data: EvaluationRequest):

    agent = HallucinationDetectionAgent()

    result = agent.evaluate(
        data.response,
        data.reference_answer
    )

    return result

@router.post("/all")
def evaluate_all(data: EvaluationRequest):

    relevance_agent = RelevanceJudgeAgent()
    accuracy_agent = AccuracyJudgeAgent()
    hallucination_agent = HallucinationDetectionAgent()


    relevance_result = relevance_agent.evaluate(
        data.question,
        data.response
    )


    accuracy_result = accuracy_agent.evaluate(
        data.response,
        data.reference_answer
    )


    hallucination_result = hallucination_agent.evaluate(
        data.response,
        data.reference_answer
    )


    return {

        "relevance": relevance_result,

        "accuracy": accuracy_result,

        "hallucination": hallucination_result

    }