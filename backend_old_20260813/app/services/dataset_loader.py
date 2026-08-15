from app.services.truthfulqa_loader import load_truthfulqa
from app.services.squad_loader import load_squad


def load_datasets(
    truthfulqa_limit: int = None,
    squad_limit: int = None,
):
    """
    Load and combine all benchmark datasets
    into one unified list.
    """

    truthfulqa_data = load_truthfulqa(
        limit=truthfulqa_limit
    )

    squad_data = load_squad(
        limit=squad_limit
    )

    combined_data = truthfulqa_data + squad_data

    return combined_data