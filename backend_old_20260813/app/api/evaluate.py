from fastapi import APIRouter

from app.schemas.request import EvaluationRequest

from app.agents.relevance_agent import RelevanceJudgeAgent
from app.agents.accuracy_agent import AccuracyJudgeAgent
from app.agents.hallucination_agent import HallucinationDetectionAgent
from app.agents.completeness_agent import CompletenessJudge

from app.orchestration.orchestrator import EvaluationOrchestrator


router = APIRouter()


# ----------------------------------------------------------------------
# Single-dimension endpoints
# ----------------------------------------------------------------------
# These stay simple and don't need the orchestrator: each one runs exactly
# one agent and doesn't need RAG fallback or cross-agent sequencing.
# Note: unlike /accuracy, /hallucination, /all and /verdict, these do NOT
# get the RAG fallback (there's no reference_answer input to resolve for
# relevance/completeness, and giving accuracy/hallucination fallback here
# too would make single-dimension and combined endpoints behave
# inconsistently for the same request). Use /evaluate/all for RAG-aware
# accuracy/hallucination scoring.

@router.post("/relevance")
def evaluate_relevance(data: EvaluationRequest):
    agent = RelevanceJudgeAgent()
    return agent.evaluate(data.question, data.response)


@router.post("/accuracy")
def evaluate_accuracy(data: EvaluationRequest):
    agent = AccuracyJudgeAgent()
    return agent.evaluate(data.response, data.reference_answer)


@router.post("/hallucination")
def evaluate_hallucination(data: EvaluationRequest):
    agent = HallucinationDetectionAgent()
    return agent.evaluate(data.response, data.reference_answer)


@router.post("/completeness")
def evaluate_completeness(data: EvaluationRequest):
    agent = CompletenessJudge()
    return agent.evaluate(data.question, data.response)


# ----------------------------------------------------------------------
# Full-pipeline endpoints -- both delegate to EvaluationOrchestrator
# instead of duplicating agent sequencing inline (previously /verdict and
# /all each independently instantiated and called all five agents).
# ----------------------------------------------------------------------

@router.post("/verdict")
def evaluate_verdict(data: EvaluationRequest):
    orchestrator = EvaluationOrchestrator()
    return orchestrator.run_verdict_only(
        data.question,
        data.response,
        data.reference_answer,
    )


@router.post("/all")
def evaluate_all(data: EvaluationRequest):
    orchestrator = EvaluationOrchestrator()
    return orchestrator.run_all(
        data.question,
        data.response,
        data.reference_answer,
    )
