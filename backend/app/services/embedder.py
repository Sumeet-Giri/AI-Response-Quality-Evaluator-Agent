from sentence_transformers import SentenceTransformer  # type: ignore[import]

# Load the model only once
model = SentenceTransformer("all-MiniLM-L6-v2")


def generate_embeddings(chunks):
    """
    Generate embeddings for text chunks.
    """

    embedded_chunks = []

    for chunk in chunks:

        embedding = model.encode(chunk["text"]).tolist()

        embedded_chunks.append(
            {
                "text": chunk["text"],
                "embedding": embedding,
                "metadata": chunk["metadata"]
            }
        )

    return embedded_chunks

def generate_query_embedding(query: str):
    """
    Generate embedding for a user's query.
    """

    return model.encode(query).tolist()