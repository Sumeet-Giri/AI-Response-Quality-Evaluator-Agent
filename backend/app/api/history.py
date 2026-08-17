"""
Evaluation History API
------------------------
Read-side endpoints backing the Milestone 4 Dashboard. Every evaluation
made through /evaluate/all (single or batch) is already persisted
automatically by EvaluationOrchestrator -- these endpoints just query
that history back out, aggregated for the views the Dashboard needs.

- /history/summary          overall stats across everything ever evaluated
- /history/batches          one row per batch run (the "trends across
                             batch evaluations" data source)
- /history/systems          one row per tagged AI system (for comparing
                             two or more systems side by side)
- /history/runs             raw rows, filterable, for drill-down/export
- /history/filter-options   distinct systems/datasets/modes + date bounds,
                             for populating the Dashboard's filter widgets

/summary, /batches, /systems, and /runs all accept the same optional
filters: system_name, mode, dataset (maps to batch_label), date_from,
date_to (both YYYY-MM-DD). Omitting all of them returns the unfiltered
view exactly as before this filtering support was added.
"""

from fastapi import APIRouter, Query

from app.services import history_store

router = APIRouter()


@router.get("/summary")
def get_summary(
    system_name: str | None = None,
    mode: str | None = None,
    dataset: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
):
    return history_store.get_overall_summary(
        system_name=system_name,
        mode=mode,
        dataset=dataset,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/batches")
def get_batches(
    system_name: str | None = None,
    dataset: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = Query(default=100, le=1000),
):
    return history_store.get_batch_summaries(
        system_name=system_name,
        dataset=dataset,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )


@router.get("/systems")
def get_systems(
    mode: str | None = None,
    dataset: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
):
    return history_store.get_system_summaries(
        mode=mode,
        dataset=dataset,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/runs")
def get_runs(
    system_name: str | None = None,
    batch_id: str | None = None,
    mode: str | None = None,
    dataset: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = Query(default=500, le=5000),
):
    return history_store.get_runs(
        system_name=system_name,
        batch_id=batch_id,
        mode=mode,
        dataset=dataset,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )


@router.get("/filter-options")
def get_filter_options():
    return history_store.get_filter_options()
