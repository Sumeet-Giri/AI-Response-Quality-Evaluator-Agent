from fastapi import APIRouter

from app.schemas.request import EvaluationRequest

from agents.relevance_agent import RelevanceJudgeAgent
from agents.accuracy_agent import AccuracyJudgeAgent
from agents.hallucination_agent import HallucinationDetectionAgent
from agents.completeness_agent import CompletenessJudge
from agents.verdict_agent import VerdictAgent


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

@router.post("/completeness")
def evaluate_completeness(data: EvaluationRequest):

    agent = CompletenessJudge()

    result = agent.evaluate(
        data.question,
        data.response
    )

    return result

@router.post("/verdict")
def evaluate_verdict(data: EvaluationRequest):

    # Initialize all agents
    relevance_agent = RelevanceJudgeAgent()
    accuracy_agent = AccuracyJudgeAgent()
    hallucination_agent = HallucinationDetectionAgent()
    completeness_agent = CompletenessJudge()
    verdict_agent = VerdictAgent()

    # Relevance Evaluation
    relevance_result = relevance_agent.evaluate(
        data.question,
        data.response
    )

    # Accuracy Evaluation
    accuracy_result = accuracy_agent.evaluate(
        data.response,
        data.reference_answer
    )

    # Hallucination Evaluation
    hallucination_result = hallucination_agent.evaluate(
        data.response,
        data.reference_answer
    )

    # Completeness Evaluation
    completeness_result = completeness_agent.evaluate(
        data.question,
        data.response
    )

    # Verdict Evaluation
    verdict_result = verdict_agent.evaluate(
        relevance_result,
        accuracy_result,
        hallucination_result,
        completeness_result
    )

    return verdict_result

@router.post("/all")
def evaluate_all(data: EvaluationRequest):

    # Initialize all agents
    relevance_agent = RelevanceJudgeAgent()
    accuracy_agent = AccuracyJudgeAgent()
    hallucination_agent = HallucinationDetectionAgent()
    completeness_agent = CompletenessJudge()
    verdict_agent = VerdictAgent()

    # Relevance Evaluation
    relevance_result = relevance_agent.evaluate(
        data.question,
        data.response
    )

    # Accuracy Evaluation
    accuracy_result = accuracy_agent.evaluate(
        data.response,
        data.reference_answer
    )

    # Hallucination Evaluation
    hallucination_result = hallucination_agent.evaluate(
        data.response,
        data.reference_answer
    )

    # Completeness Evaluation
    completeness_result = completeness_agent.evaluate(
        data.question,
        data.response
    )

    # Verdict Evaluation
    verdict_result = verdict_agent.evaluate(
    relevance_result,
    accuracy_result,
    hallucination_result,
    completeness_result
    )

    # Return all results
    return {

        "relevance": relevance_result,

        "accuracy": accuracy_result,

        "hallucination": hallucination_result,

        "completeness": completeness_result,

        "verdict": verdict_result

    }