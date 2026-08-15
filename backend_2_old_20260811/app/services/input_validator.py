"""
File input validation.

question/response/reference_answer validation now lives directly on
EvaluationRequest (app/schemas/request.py) via Pydantic field validators --
that's the idiomatic FastAPI way to reject bad input, and having a second,
separate validate_input() doing the same job was a real bug: it checked
`request.ai_response`, a field name that never matched the actual
EvaluationRequest schema (`response`), so it would have raised
AttributeError if it had ever actually been called from a live endpoint.
It never was (only from now-deleted app/api/routes.py) -- but rather than
leave a second, broken, redundant validator sitting in the codebase, this
file is now scoped to what it does uniquely: file-extension validation,
which will matter again once document/PDF input is rebuilt (Milestone 4+).
"""

from pathlib import Path

ALLOWED_EXTENSIONS = [".pdf", ".txt"]


def validate_file(filename: str):

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Only PDF and TXT files are allowed."
        )

    return True
