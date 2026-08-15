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

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


DB_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "evaluation_history.db"
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
# Read-side queries
# --------------------------------------------------------------------

def get_runs(
    system_name: Optional[str] = None,
    batch_id: Optional[str] = None,
    mode: Optional[str] = None,
    limit: int = 500,
) -> list[dict]:

    query = """
        SELECT *
        FROM evaluation_records
        WHERE 1=1
    """

    params: list = []

    if system_name:
        query += " AND system_name = ?"
        params.append(system_name)

    if batch_id:
        query += " AND batch_id = ?"
        params.append(batch_id)

    if mode:
        query += " AND mode = ?"
        params.append(mode)

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


def get_overall_summary() -> dict:
    """
    Return overall evaluation statistics.

    high_hallucination_count is retained for backward compatibility.
    The new claim-level hallucination metrics are also aggregated.
    """

    with _connect() as conn:

        row = conn.execute(
            """
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
            """
        ).fetchone()

        return dict(row) if row else {}


def get_batch_summaries(
    limit: int = 100
) -> list[dict]:
    """
    Return one row per distinct batch run.
    """

    with _connect() as conn:

        rows = conn.execute(
            """
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
                ) AS fail_count

            FROM evaluation_records

            WHERE
                mode = 'batch'
                AND batch_id IS NOT NULL

            GROUP BY batch_id

            ORDER BY started_at DESC

            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]


def get_system_summaries() -> list[dict]:
    """
    Return one row per distinct AI system.
    """

    with _connect() as conn:

        rows = conn.execute(
            """
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

            GROUP BY system_name

            ORDER BY total_evaluations DESC
            """
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