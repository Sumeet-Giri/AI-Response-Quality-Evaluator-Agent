from datasets import load_dataset


def load_truthfulqa(limit: int = None):
    """
    Load TruthfulQA dataset and normalize it into
    the project's internal format.
    """

    dataset = load_dataset(
        "truthfulqa/truthful_qa",
        "generation"
    )

    records = dataset["validation"]

    if limit:
        records = records.select(range(limit))

    normalized_data = []

    for record in records:
        normalized_data.append(
    {
        "question": record["question"],
        "answer": record["best_answer"],
        "context": None,          # ← Add this
        "source": record["source"],
        "dataset": "truthfulqa"
    }
)
        

    return normalized_data