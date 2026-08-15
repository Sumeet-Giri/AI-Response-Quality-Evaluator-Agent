"""
Evaluation Orchestrator
------------------------
Single place responsible for running the full multi-agent evaluation
pipeline in the correct order: Relevance -> Accuracy -> Hallucination ->
Completeness -> Verdict.

Why this exists: previously, `app/api/evaluate.py`'s `/verdict` and `/all`
route handlers each independently instantiated all five agents and called
them in the same sequence -- duplicated, near-identical code in two places.
Both endpoints now call into this class instead, so the sequencing lives in
exactly one place, and can be tested (and reused, e.g. by a future
background job or CLI tool) independently of FastAPI.

This is also where the RAG fallback lives: if the caller doesn't supply a
reference_answer, the orchestrator retrieves the closest passage from the
reference knowledge base (ChromaDB, seeded from TruthfulQA/SQuAD) and uses
that as the reference for Accuracy and Hallucination scoring instead of
leaving them nothing to compare against. This is what makes
"reference answer OR retrieved evidence" -- the original scope for those
two agents -- actually true of the running system, not just of code that
exists somewhere in the repo.
"""

from app.agents.relevance_agent import RelevanceJudgeAgent
from app.agents.accuracy_agent import AccuracyJudgeAgent
from app.agents.hallucination_agent import HallucinationDetectionAgent
from app.agents.completeness_agent import CompletenessJudge
from app.agents.verdict_agent import VerdictAgent

from app.services.retriever import retrieve_reference
from app.services import history_store


class EvaluationOrchestrator:

    def __init__(self):
        # Agents hold no expensive per-instance state (the shared
        # SentenceTransformer model lives in app.services.embedder as a
        # module-level singleton), so constructing them per-orchestrator-
        # instance is cheap. See backend architecture review, Performance
        # Review, for why this is fine for these four but was NOT fine for
        # CompletenessJudge's now-removed unused model load.
        self.relevance_agent = RelevanceJudgeAgent()
        self.accuracy_agent = AccuracyJudgeAgent()
        self.hallucination_agent = HallucinationDetectionAgent()
        self.completeness_agent = CompletenessJudge()
        self.verdict_agent = VerdictAgent()

    # ------------------------------------------------------------------
    # RAG fallback
    # ------------------------------------------------------------------
    def _resolve_reference(
        self,
        question: str,
        reference_answer: str
    ) -> tuple[str, dict]:
        """
        Returns (reference_text_to_use, rag_metadata).

        - If the caller supplied a non-blank reference_answer, it is used
          as-is (user-supplied evidence always takes priority over
          retrieval) and rag_metadata records that.
        - Otherwise, retrieves the single closest passage from the
          knowledge base and uses it as the reference.
        - If retrieval finds nothing (knowledge base not yet seeded, or
          any retrieval-layer problem), degrades gracefully to an empty
          reference rather than failing the request -- Accuracy and
          Hallucination will then score conservatively low, exactly as
          they did before RAG was wired in, instead of the whole
          evaluation erroring out.
        """
        if reference_answer and reference_answer.strip():
            return reference_answer.strip(), {"source": "user_supplied"}

        retrieved = retrieve_reference(question, top_k=1)

        if retrieved is not None:
            return retrieved["text"], {
                "source": "retrieved",
                "metadata": retrieved.get("metadata", {}),
                "similarity_distance": retrieved.get("distance"),
            }

        return "", {
            "source": "none",
            "reason": (
                "No reference_answer supplied and no retrievable evidence "
                "was found in the knowledge base."
            ),
        }

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------
    def run_all(
        self,
        question: str,
        response: str,
        reference_answer: str = "",
        system_name: str = "Unspecified",
        batch_id: str | None = None,
        batch_label: str | None = None,
    ) -> dict:

        resolved_reference, rag_info = self._resolve_reference(
            question,
            reference_answer
        )

        relevance_result = self.relevance_agent.evaluate(
            question,
            response
        )

        accuracy_result = self.accuracy_agent.evaluate(
            response,
            resolved_reference
        )

        hallucination_result = self.hallucination_agent.evaluate(
            response,
            resolved_reference
        )

        completeness_result = self.completeness_agent.evaluate(
            question,
            response
        )

        verdict_result = self.verdict_agent.evaluate(
            relevance_result,
            accuracy_result,
            hallucination_result,
            completeness_result,
        )

        # Persisted automatically -- this is what makes the Milestone 4
        # Dashboard's cross-batch trends and system-vs-system comparison
        # possible. Best-effort (see history_store.record_evaluation):
        # a persistence failure here can never break the response below.
        history_store.record_evaluation(
            mode="batch" if batch_id else "single",
            question=question,
            response=response,
            reference_answer=resolved_reference,
            rag_source=rag_info.get("source", "none"),

            relevance_score=relevance_result.score,
            accuracy_score=accuracy_result.score,

            # Existing hallucination score
            hallucination_score=hallucination_result.hallucination_score,

            # New claim-level hallucination metrics
            total_claims=hallucination_result.total_claims,
            supported_claims_count=(
                hallucination_result.supported_claims_count
            ),
            hallucinated_claims_count=(
                hallucination_result.hallucinated_claims_count
            ),
            hallucination_rate=(
                hallucination_result.hallucination_rate
            ),

            completeness_score=completeness_result.completeness_score,
            overall_score=verdict_result.overall_score,
            final_verdict=verdict_result.final_verdict,
            quality_gate_passed=verdict_result.quality_gate_passed,

            system_name=system_name,
            batch_id=batch_id,
            batch_label=batch_label,
        )

        return {
            "relevance": relevance_result,
            "accuracy": accuracy_result,
            "hallucination": hallucination_result,
            "completeness": completeness_result,
            "verdict": verdict_result,
            "rag": rag_info,
        }

    def run_verdict_only(
        self,
        question: str,
        response: str,
        reference_answer: str = ""
    ):
        """
        Used by /evaluate/verdict, which historically returns just the
        VerdictResult (not the full breakdown) -- kept identical to that
        existing response contract so nothing downstream has to change.
        """

        return self.run_all(
            question,
            response,
            reference_answer
        )["verdict"]