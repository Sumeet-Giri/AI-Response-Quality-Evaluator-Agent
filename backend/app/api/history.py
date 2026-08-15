"""
Evaluation History API
------------------------
Read-side endpoints backing the Milestone 4 Dashboard. Every evaluation
made through /evaluate/all (single or batch) is already persisted
automatically by EvaluationOrchestrator -- these endpoints just query
that history back out, aggregated for the views the Dashboard needs:

- /history/summary        overall stats across everything ever evaluated
- /history/batches        one row per batch run (the "trends across
                           batch evaluations" data source)
- /history/systems        one row per tagged AI system (for comparing
                           two or more systems side by side)
- /history/runs           raw rows, filterable, for drill-down/export
"""

from fastapi import APIRouter, Query

from app.services import history_store

router = APIRouter()


@router.get("/summary")
def get_summary():
    return history_store.get_overall_summary()


@router.get("/batches")
def get_batches(limit: int = Query(default=100, le=1000)):
    return history_store.get_batch_summaries(limit=limit)


@router.get("/systems")
def get_systems():
    return history_store.get_system_summaries()


@router.get("/runs")
def get_runs(
    system_name: str | None = None,
    batch_id: str | None = None,
    mode: str | None = None,
    limit: int = Query(default=500, le=5000),
):
    return history_store.get_runs(
        system_name=system_name,
        batch_id=batch_id,
        mode=mode,
        limit=limit,
    )
