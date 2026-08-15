"""
CSV Parser & Validator
-----------------------
Handles everything between "user uploaded a file" and "we have a clean
DataFrame safe to run through the evaluation pipeline":

- Robust CSV parsing (encoding issues, malformed files)
- Case-insensitive / whitespace-tolerant column matching
- Required column enforcement (question, response)
- Optional reference_answer column (created empty if missing)
- Missing-value handling for required fields (dropped, but counted &
  reported rather than silently discarded)

This module never raises for "expected" bad input — it always returns a
(df, errors, warnings) tuple so the calling page can render feedback
gracefully instead of crashing.
"""

import io
import pandas as pd

REQUIRED_COLUMNS = ["question", "response"]
OPTIONAL_COLUMNS = ["reference_answer"]
MAX_RECOMMENDED_ROWS = 500


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df


def load_and_validate_csv(uploaded_file) -> tuple[pd.DataFrame | None, list[str], list[str]]:
    """
    Parses an uploaded CSV (Streamlit UploadedFile or file-like object) and
    validates it against the expected batch-evaluation schema.

    Returns:
        (df, errors, warnings)
        - df is None if the file could not be parsed or is missing required
          columns; otherwise a cleaned DataFrame ready for evaluation.
        - errors: problems that block evaluation entirely.
        - warnings: non-blocking issues (missing values dropped, oversized
          file truncated, etc.) worth surfacing to the user.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # ---- Parse ----
    raw_bytes = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
    df = None
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(io.BytesIO(raw_bytes), encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            errors.append(f"Could not parse the file as CSV: {e}")
            return None, errors, warnings

    if df is None:
        errors.append(
            "Could not decode the file with common encodings (UTF-8, Latin-1). "
            "Please re-save the CSV with UTF-8 encoding and try again."
        )
        return None, errors, warnings

    if df.empty:
        errors.append("The uploaded CSV has no rows.")
        return None, errors, warnings

    df = _normalize_columns(df)

    # ---- Required columns ----
    missing_required = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_required:
        errors.append(
            "Missing required column(s): "
            + ", ".join(f"`{c}`" for c in missing_required)
            + f". Found columns: {', '.join(df.columns)}"
        )
        return None, errors, warnings

    # ---- Optional columns ----
    for c in OPTIONAL_COLUMNS:
        if c not in df.columns:
            df[c] = ""
            warnings.append(f"Column `{c}` was not found — treating it as empty for every row.")

    # ---- Missing values in required fields ----
    # NOTE: pandas 3.0's default string dtype keeps missing values as NA even
    # after .astype(str) (unlike pre-3.0 object columns, where NaN becomes the
    # literal text "nan"). Filling NA -> "" *before* stringifying handles both
    # pandas versions correctly.
    before = len(df)
    df["question"] = df["question"].fillna("").astype(str).str.strip()
    df["response"] = df["response"].fillna("").astype(str).str.strip()
    df["reference_answer"] = df["reference_answer"].fillna("").astype(str).str.strip()
    df.loc[df["reference_answer"].str.lower() == "nan", "reference_answer"] = ""

    bad_mask = (
        df["question"].str.lower().isin(["", "nan", "none", "null"])
        | df["response"].str.lower().isin(["", "nan", "none", "null"])
    )
    dropped = int(bad_mask.sum())
    if dropped:
        df = df.loc[~bad_mask].reset_index(drop=True)
        warnings.append(
            f"Dropped {dropped} row(s) with a missing `question` or `response` value "
            f"(out of {before} total rows)."
        )

    if df.empty:
        errors.append("After removing rows with missing question/response values, no rows remained.")
        return None, errors, warnings

    # ---- Size guardrail ----
    if len(df) > MAX_RECOMMENDED_ROWS:
        warnings.append(
            f"This file has {len(df)} rows — that's above the recommended cap of "
            f"{MAX_RECOMMENDED_ROWS} for a single run (each row is a sequential API call, "
            "so very large files can take a long time). Consider splitting it, or proceed "
            "and let it run."
        )

    return df.reset_index(drop=True), errors, warnings


def sample_dataset() -> pd.DataFrame:
    """Small built-in dataset so the page is demoable without a real CSV."""
    return pd.DataFrame(
        [
            {"question": "What causes rainbows?",
             "response": "Rainbows form when sunlight is refracted and reflected inside water droplets.",
             "reference_answer": "Refraction and reflection of light in water droplets."},
            {"question": "Who wrote Hamlet?",
             "response": "Hamlet was written by William Shakespeare in the early 1600s.",
             "reference_answer": "William Shakespeare."},
            {"question": "What is the capital of Australia?",
             "response": "The capital of Australia is Sydney.",
             "reference_answer": "Canberra."},
            {"question": "How does photosynthesis work?",
             "response": "Plants use sunlight, water, and CO2 to produce glucose and oxygen via chlorophyll.",
             "reference_answer": "Conversion of light energy into chemical energy using chlorophyll."},
            {"question": "What is the speed of light?",
             "response": "The speed of light in vacuum is approximately 300,000 km/s.",
             "reference_answer": "299,792 km/s in a vacuum."},
            {"question": "What is the boiling point of water?",
             "response": "Water boils at 100 degrees Celsius at sea level atmospheric pressure.",
             "reference_answer": "100°C (212°F) at standard atmospheric pressure."},
            {"question": "Who painted the Mona Lisa?",
             "response": "The Mona Lisa was painted by Leonardo da Vinci in the early 16th century.",
             "reference_answer": "Leonardo da Vinci."},
            {"question": "What is machine learning?",
             "response": "Bananas are a good source of potassium and are grown in tropical climates.",
             "reference_answer": "Machine learning is a field of AI where systems learn patterns from data."},
        ]
    )
