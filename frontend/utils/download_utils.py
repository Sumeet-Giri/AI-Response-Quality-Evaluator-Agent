"""
Download Utils
--------------
Serialization helpers for the batch evaluation export buttons. Kept
separate from the page so the same helpers can be reused anywhere else
results need to be exported.
"""

import io
import json
import pandas as pd


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Results") -> bytes:
    """
    Renders the results table to a styled-enough .xlsx (auto-width columns).
    Requires openpyxl (declared in frontend/requirements.txt).
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        worksheet = writer.sheets[sheet_name]
        for i, col in enumerate(df.columns):
            max_len = max(
                [len(str(col))] + [len(str(v)) for v in df[col].astype(str).tolist()]
            )
            worksheet.column_dimensions[chr(65 + i) if i < 26 else "A"].width = min(60, max_len + 2)
    buffer.seek(0)
    return buffer.getvalue()


def to_json_bytes(full_rows: list[dict]) -> bytes:
    """Full nested per-row results (all four agents + verdict), for reproducibility / audits."""
    return json.dumps(full_rows, indent=2, default=str).encode("utf-8")
