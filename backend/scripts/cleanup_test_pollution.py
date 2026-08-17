"""
One-time cleanup: removes evaluation history rows written by an earlier
version of the test suite, which (before this fix) wrote directly into
the real evaluation_history.db instead of an isolated test database.

Only deletes rows whose system_name EXACTLY matches one of the known
test-fixture names below -- strings that only ever originate from
tests/test_e2e_integration.py, never from real usage. Nothing else is
touched: "Unspecified", "GPT-4", "Claude-3", or any other system name you
tagged yourself is left completely alone, since there's no reliable way
to distinguish real untagged evaluations from test-injected ones under
the generic "Unspecified" label without risking deleting real data.

Run once, from the backend/ directory:
    python scripts/cleanup_test_pollution.py
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "evaluation_history.db"

KNOWN_TEST_FIXTURE_SYSTEM_NAMES = [
    "IntegrationTestSystem",
    "BatchTestSystem",
    "BreakdownTestSystem",
    "FilterTestSystemA",
    "FilterTestSystemB",
    "FilterOptionsTestSystem",
]


def main():
    if not DB_PATH.exists():
        print(f"No database found at {DB_PATH} -- nothing to clean up.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    placeholders = ",".join("?" for _ in KNOWN_TEST_FIXTURE_SYSTEM_NAMES)

    rows = conn.execute(
        f"SELECT system_name, COUNT(*) as n FROM evaluation_records "
        f"WHERE system_name IN ({placeholders}) GROUP BY system_name",
        KNOWN_TEST_FIXTURE_SYSTEM_NAMES,
    ).fetchall()

    if not rows:
        print("No test-fixture pollution found. Nothing to delete.")
        conn.close()
        return

    print("The following test-fixture rows will be deleted:")
    total = 0
    for row in rows:
        print(f"  - {row['system_name']}: {row['n']} row(s)")
        total += row["n"]
    print(f"\nTotal: {total} row(s).")
    print("Nothing else (Unspecified, GPT-4, Claude-3, or any other system name) will be touched.\n")

    confirm = input("Proceed with deletion? [y/N] ").strip().lower()
    if confirm != "y":
        print("Cancelled -- no changes made.")
        conn.close()
        return

    conn.execute(
        f"DELETE FROM evaluation_records WHERE system_name IN ({placeholders})",
        KNOWN_TEST_FIXTURE_SYSTEM_NAMES,
    )
    conn.commit()
    conn.close()
    print(f"Deleted {total} test-fixture row(s). Real evaluation history is untouched.")


if __name__ == "__main__":
    main()
