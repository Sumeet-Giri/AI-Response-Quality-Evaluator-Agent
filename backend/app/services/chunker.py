def create_chunks(records):
    """
    Convert normalized dataset records into
    text chunks ready for embedding.
    """

    chunks = []

    for record in records:

        chunk_text = f"""
Question:
{record["question"]}

Context:
{record["context"] if record["context"] else "N/A"}

Answer:
{record["answer"]}
"""

        chunk = {
            "text": chunk_text.strip(),
            "metadata": {
                "dataset": record["dataset"],
                "source": record["source"]
            }
        }

        chunks.append(chunk)

    return chunks