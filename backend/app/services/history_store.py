"""
Evaluation History Store (SQLite)
-----------------------------------
Persists every evaluation (single or batch) so the Milestone 4 Dashboard
can show real trends across runs, not just the current browser session.

This module stores both the existing evaluation scores and claim-level
hallucination metrics.

Hallucination metrics:
- total_claims
- supported_claims_count
- hallucinated_claims_count
- hallucination_rate

The existing hallucination_score is preserved because it is used by the
Verdict Agent and existing dashboard logic.
"""

import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# DB_PATH is overridable via the EVAL_HISTORY_DB_PATH environment variable.
# Real usage (uvicorn app.main:app) never sets this, so it resolves to the
# same backend/evaluation_history.db path as always -- zero behavior
# change for the running application.
#
# conftest.py sets this env var to an isolated temp file before any app
# module is imported, so the test suite (which boots the real app via
# FastAPI's TestClient in test_e2e_integration.py) can never again write
# test fixture data into the real database. This overridability was added
# specifically because it wasn't there before: running `pytest` used to
# silently inject system names like "BatchTestSystem" and
# "IntegrationTestSystem" into the live Dashboard's real evaluation
# history, which is a serious testing-hygiene defect, not a cosmetic one.
_env_path = os.environ.get("EVAL_HISTORY_DB_PATH")
DB_PATH = (
    Path(_env_path)
    if _env_path
    else Path(__file__).resolve().parent.parent.parent / "evaluation_history.db"
)


# --------------------------------------------------------------------
# Database schema
# --------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS evaluation_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    mode TEXT NOT NULL,
    batch_id TEXT,
    batch_label TEXT,
    system_name TEXT NOT NULL DEFAULT 'Unspecified',

    question TEXT NOT NULL,
    response TEXT NOT NULL,
    reference_answer TEXT,
    rag_source TEXT,

    relevance_score REAL,
    accuracy_score REAL,
    hallucination_score REAL,

    total_claims INTEGER,
    supported_claims_count INTEGER,
    hallucinated_claims_count INTEGER,
    hallucination_rate REAL,

    completeness_score REAL,
    overall_score REAL,
    final_verdict TEXT,
    quality_gate_passed INTEGER
);

CREATE INDEX IF NOT EXISTS idx_batch_id
ON evaluation_records(batch_id);

CREATE INDEX IF NOT EXISTS idx_system_name
ON evaluation_records(system_name);

CREATE INDEX IF NOT EXISTS idx_created_at
ON evaluation_records(created_at);
"""


# --------------------------------------------------------------------
# Database migration
# --------------------------------------------------------------------

def _migrate_database(conn):
    """
    Add newly introduced columns to an existing evaluation_records table.

    SQLite does not support adding columns through
    CREATE TABLE IF NOT EXISTS when the table already exists, so we
    explicitly inspect the existing schema and add missing columns.

    This migration is idempotent and safe to run repeatedly.
    """

    existing_columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(evaluation_records)"
        ).fetchall()
    }

    new_columns = {
        "total_claims": "INTEGER",
        "supported_claims_count": "INTEGER",
        "hallucinated_claims_count": "INTEGER",
        "hallucination_rate": "REAL",
    }

    for column_name, column_type in new_columns.items():

        if column_name not in existing_columns:

            conn.execute(
                f"""
                ALTER TABLE evaluation_records
                ADD COLUMN {column_name} {column_type}
                """
            )


# --------------------------------------------------------------------
# Database connection
# --------------------------------------------------------------------

@contextmanager
def _connect():
    """
    Open a short-lived SQLite connection.

    The schema is ensured and migrations are applied every time a
    connection is opened. This keeps the module safe even if init_db()
    was not explicitly called first.
    """

    conn = sqlite3.connect(
        DB_PATH,
        timeout=10
    )

    conn.row_factory = sqlite3.Row

    try:
        # Create table/indexes if necessary.
        conn.executescript(_SCHEMA)

        # Migrate existing databases if necessary.
        _migrate_database(conn)

        yield conn

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# --------------------------------------------------------------------
# Database initialization
# --------------------------------------------------------------------

def init_db():
    """
    Create the evaluation history database/table if it does not exist.

    Also applies migrations for existing databases.
    """

    with _connect() as conn:
        conn.executescript(_SCHEMA)
        _migrate_database(conn)


# --------------------------------------------------------------------
# Batch helpers
# --------------------------------------------------------------------

def new_batch_id() -> str:
    """
    Generate a short unique identifier for a batch evaluation.
    """

    return uuid.uuid4().hex[:12]


# --------------------------------------------------------------------
# Write-side
# --------------------------------------------------------------------

def record_evaluation(
    *,
    mode: str,
    question: str,
    response: str,
    reference_answer: str,
    rag_source: str,

    relevance_score,
    accuracy_score,
    hallucination_score,

    total_claims,
    supported_claims_count,
    hallucinated_claims_count,
    hallucination_rate,

    completeness_score,
    overall_score,
    final_verdict: str,
    quality_gate_passed: bool,

    system_name: str = "Unspecified",
    batch_id: Optional[str] = None,
    batch_label: Optional[str] = None,
) -> None:
    """
    Persist one evaluation result.

    Hallucination metrics are stored at claim level:

        total_claims
        supported_claims_count
        hallucinated_claims_count
        hallucination_rate

    Persistence is intentionally best-effort. A database failure must
    never break the actual evaluation response.
    """

    try:

        with _connect() as conn:

            conn.execute(
                """
                INSERT INTO evaluation_records (
                    created_at,
                    mode,
                    batch_id,
                    batch_label,
                    system_name,

                    question,
                    response,
                    reference_answer,
                    rag_source,

                    relevance_score,
                    accuracy_score,
                    hallucination_score,

                    total_claims,
                    supported_claims_count,
                    hallucinated_claims_count,
                    hallucination_rate,

                    completeness_score,
                    overall_score,
                    final_verdict,
                    quality_gate_passed
                )
                VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?
                )
                """,
                (
                    datetime.now(timezone.utc).isoformat(),

                    mode,
                    batch_id,
                    batch_label,
                    system_name or "Unspecified",

                    question,
                    response,
                    reference_answer,
                    rag_source,

                    relevance_score,
                    accuracy_score,
                    hallucination_score,

                    total_claims,
                    supported_claims_count,
                    hallucinated_claims_count,
                    hallucination_rate,

                    completeness_score,
                    overall_score,
                    final_verdict,

                    1 if quality_gate_passed else 0,
                ),
            )

    except Exception:
        # History persistence is best-effort by design.
        # Never allow a database problem to break evaluation.
        pass


# --------------------------------------------------------------------
# Shared filter builder
# --------------------------------------------------------------------
# Every read-side query below accepts the same optional filters (system,
# evaluation mode, dataset, date range) and builds its WHERE clause
# through this one helper, so filtering behaves identically everywhere
# and isn't reimplemented per-query.
#
# "Dataset" filters on batch_label -- there is no dedicated dataset
# column in the schema today; batch_label (e.g. "Trivia set v1") is the
# closest existing concept. A true dataset_name field, distinct from a
# free-text run label, would be a schema addition if that distinction
# ever needs to be stricter than it is now.

def _build_filters(
    system_name: Optional[str] = None,
    mode: Optional[str] = None,
    dataset: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> tuple[str, list]:
    clauses = []
    params: list = []

    if system_name:
        clauses.append("system_name = ?")
        params.append(system_name)

    if mode:
        clauses.append("mode = ?")
        params.append(mode)

    if dataset:
        clauses.append("batch_label = ?")
        params.append(dataset)

    if date_from:
        # created_at is an ISO timestamp; a date-only lower bound
        # correctly includes the entire day via string comparison.
        clauses.append("created_at >= ?")
        params.append(date_from)

    if date_to:
        # Append time-of-day so the upper bound includes the whole day,
        # not just 00:00:00 of that date.
        clauses.append("created_at <= ?")
        params.append(f"{date_to}T23:59:59.999999")

    where = (" AND " + " AND ".join(clauses)) if clauses else ""
    return where, params


def get_filter_options() -> dict:
    """
    Distinct values for populating the Dashboard's filter dropdowns --
    every system name, dataset/batch label, and mode ever recorded, plus
    the earliest/latest evaluation timestamps for a sensible default date
    range.
    """
    with _connect() as conn:
        systems = [
            r["system_name"] for r in conn.execute(
                "SELECT DISTINCT system_name FROM evaluation_records ORDER BY system_name"
            ).fetchall()
        ]
        datasets = [
            r["batch_label"] for r in conn.execute(
                "SELECT DISTINCT batch_label FROM evaluation_records "
                "WHERE batch_label IS NOT NULL AND batch_label != '' ORDER BY batch_label"
            ).fetchall()
        ]
        modes = [
            r["mode"] for r in conn.execute(
                "SELECT DISTINCT mode FROM evaluation_records ORDER BY mode"
            ).fetchall()
        ]
        bounds = conn.execute(
            "SELECT MIN(created_at) AS earliest, MAX(created_at) AS latest FROM evaluation_records"
        ).fetchone()

        return {
            "systems": systems,
            "datasets": datasets,
            "modes": modes,
            "earliest": bounds["earliest"] if bounds else None,
            "latest": bounds["latest"] if bounds else None,
        }


def get_runs(
    system_name: Optional[str] = None,
    batch_id: Optional[str] = None,
    mode: Optional[str] = None,
    dataset: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 500,
) -> list[dict]:

    where, params = _build_filters(system_name, mode, dataset, date_from, date_to)

    query = f"""
        SELECT *
        FROM evaluation_records
        WHERE 1=1 {where}
    """

    if batch_id:
        query += " AND batch_id = ?"
        params.append(batch_id)

    query += """
        ORDER BY created_at DESC
        LIMIT ?
    """

    params.append(limit)

    with _connect() as conn:

        rows = conn.execute(
            query,
            params
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]


def get_overall_summary(
    system_name: Optional[str] = None,
    mode: Optional[str] = None,
    dataset: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> dict:
    """
    Return overall evaluation statistics, optionally filtered by system,
    evaluation mode, dataset (batch_label), and/or a date range.

    high_hallucination_count and total_pass/total_fail are retained for
    backward compatibility (binary quality-gate view). pass_count /
    needs_improvement_count / fail_count is the three-way breakdown by
    final_verdict:
        Pass              -> EXCELLENT, GOOD
        Needs Improvement -> NEEDS IMPROVEMENT, POOR
        Fail              -> FAIL (quality gate failed)
    """

    where, params = _build_filters(system_name, mode, dataset, date_from, date_to)

    with _connect() as conn:

        row = conn.execute(
            f"""
            SELECT
                COUNT(*) AS total_evaluations,

                AVG(overall_score) AS avg_overall_score,

                AVG(relevance_score) AS avg_relevance,

                AVG(accuracy_score) AS avg_accuracy,

                AVG(hallucination_score) AS avg_hallucination,

                AVG(completeness_score) AS avg_completeness,

                SUM(
                    CASE
                        WHEN quality_gate_passed = 1
                        THEN 1
                        ELSE 0
                    END
                ) AS total_pass,

                SUM(
                    CASE
                        WHEN quality_gate_passed = 0
                        THEN 1
                        ELSE 0
                    END
                ) AS total_fail,

                SUM(
                    CASE
                        WHEN final_verdict IN ('EXCELLENT', 'GOOD')
                        THEN 1
                        ELSE 0
                    END
                ) AS pass_count,

                SUM(
                    CASE
                        WHEN final_verdict IN ('NEEDS IMPROVEMENT', 'POOR')
                        THEN 1
                        ELSE 0
                    END
                ) AS needs_improvement_count,

                SUM(
                    CASE
                        WHEN final_verdict = 'FAIL'
                        THEN 1
                        ELSE 0
                    END
                ) AS fail_count,

                SUM(
                    CASE
                        WHEN hallucination_score < 4
                        THEN 1
                        ELSE 0
                    END
                ) AS high_hallucination_count,

                SUM(
                    total_claims
                ) AS total_claims,

                SUM(
                    supported_claims_count
                ) AS supported_claims_count,

                SUM(
                    hallucinated_claims_count
                ) AS hallucinated_claims_count,

                AVG(
                    hallucination_rate
                ) AS avg_hallucination_rate

            FROM evaluation_records
            WHERE 1=1 {where}
            """,
            params,
        ).fetchone()

        return dict(row) if row else {}


def get_batch_summaries(
    system_name: Optional[str] = None,
    dataset: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 100
) -> list[dict]:
    """
    Return one row per distinct batch run, optionally filtered by system,
    dataset (batch_label), and/or a date range. Mode is not a filter
    parameter here since this query already restricts to mode = 'batch'.
    """

    where, params = _build_filters(system_name, None, dataset, date_from, date_to)

    with _connect() as conn:

        rows = conn.execute(
            f"""
            SELECT
                batch_id,

                MAX(batch_label)
                    AS batch_label,

                MAX(system_name)
                    AS system_name,

                MIN(created_at)
                    AS started_at,

                COUNT(*)
                    AS row_count,

                AVG(overall_score)
                    AS avg_overall_score,

                AVG(relevance_score)
                    AS avg_relevance,

                AVG(accuracy_score)
                    AS avg_accuracy,

                AVG(hallucination_score)
                    AS avg_hallucination,

                AVG(completeness_score)
                    AS avg_completeness,

                SUM(total_claims)
                    AS total_claims,

                SUM(supported_claims_count)
                    AS supported_claims_count,

                SUM(hallucinated_claims_count)
                    AS hallucinated_claims_count,

                AVG(hallucination_rate)
                    AS avg_hallucination_rate,

                SUM(
                    CASE
                        WHEN quality_gate_passed = 1
                        THEN 1
                        ELSE 0
                    END
                ) AS pass_count,

                SUM(
                    CASE
                        WHEN quality_gate_passed = 0
                        THEN 1
                        ELSE 0
                    END
                ) AS fail_count,

                SUM(
                    CASE
                        WHEN final_verdict IN ('EXCELLENT', 'GOOD')
                        THEN 1
                        ELSE 0
                    END
                ) AS pass_verdict_count,

                SUM(
                    CASE
                        WHEN final_verdict IN ('NEEDS IMPROVEMENT', 'POOR')
                        THEN 1
                        ELSE 0
                    END
                ) AS needs_improvement_count,

                SUM(
                    CASE
                        WHEN final_verdict = 'FAIL'
                        THEN 1
                        ELSE 0
                    END
                ) AS fail_verdict_count

            FROM evaluation_records

            WHERE
                mode = 'batch'
                AND batch_id IS NOT NULL
                {where}

            GROUP BY batch_id

            ORDER BY started_at DESC

            LIMIT ?
            """,
            [*params, limit],
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]


def get_system_summaries(
    mode: Optional[str] = None,
    dataset: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> list[dict]:
    """
    Return one row per distinct AI system, optionally filtered by
    evaluation mode, dataset (batch_label), and/or a date range.
    system_name itself is not a filter parameter here -- filtering by the
    exact dimension being grouped on would defeat the comparison this
    query exists to support.
    """

    where, params = _build_filters(None, mode, dataset, date_from, date_to)

    with _connect() as conn:

        rows = conn.execute(
            f"""
            SELECT
                system_name,

                COUNT(*)
                    AS total_evaluations,

                AVG(overall_score)
                    AS avg_overall_score,

                AVG(relevance_score)
                    AS avg_relevance,

                AVG(accuracy_score)
                    AS avg_accuracy,

                AVG(hallucination_score)
                    AS avg_hallucination,

                AVG(completeness_score)
                    AS avg_completeness,

                SUM(total_claims)
                    AS total_claims,

                SUM(supported_claims_count)
                    AS supported_claims_count,

                SUM(hallucinated_claims_count)
                    AS hallucinated_claims_count,

                AVG(hallucination_rate)
                    AS avg_hallucination_rate,

                SUM(
                    CASE
                        WHEN quality_gate_passed = 1
                        THEN 1
                        ELSE 0
                    END
                ) AS pass_count,

                SUM(
                    CASE
                        WHEN quality_gate_passed = 0
                        THEN 1
                        ELSE 0
                    END
                ) AS fail_count

            FROM evaluation_records
            WHERE 1=1 {where}

            GROUP BY system_name

            ORDER BY total_evaluations DESC
            """,
            params,
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]


# --------------------------------------------------------------------
# Testing/demo helper
# --------------------------------------------------------------------

def clear_all():
    """
    Delete all stored evaluation records.

    Intended for testing/demo reset only.
    """

    with _connect() as conn:
        conn.execute(
            "DELETE FROM evaluation_records"
        )