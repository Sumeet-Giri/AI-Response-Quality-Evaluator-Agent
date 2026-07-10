from datasets import load_dataset


def load_squad(limit: int = None):
    """
    Load SQuAD dataset and normalize it into
    the project's internal format.
    """

    dataset = load_dataset("rajpurkar/squad")

    records = dataset["train"]

    if limit:
        records = records.select(range(limit))

    normalized_data = []

    for record in records:

        answer = ""

        if record["answers"]["text"]:
            answer = record["answers"]["text"][0]

        normalized_data.append(
            {
                "question": record["question"],
                "answer": answer,
                "context": record["context"],
                "source": record["title"],
                "dataset": "squad"
            }
        )

    return normalized_data