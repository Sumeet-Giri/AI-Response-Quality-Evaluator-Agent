from pathlib import Path

ALLOWED_EXTENSIONS = [".pdf", ".txt"]


def validate_input(request):
    if not request.question.strip():
        raise ValueError("Question cannot be empty.")

    if not request.ai_response.strip():
        raise ValueError("AI Response cannot be empty.")

    return True


def validate_file(filename: str):

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Only PDF and TXT files are allowed."
        )

    return True