from sentence_transformers import SentenceTransformer  # type: ignore[import]

_model = None


def get_model():
    """
    Lazily load the SentenceTransformer model.

    The model is loaded only when an embedding is actually required.
    This reduces memory usage during FastAPI startup, which is important
    for low-memory deployment environments such as Render Free.
    """
    global _model

    if _model is None:
        _model = SentenceTransformer(
            "all-MiniLM-L6-v2",
            device="cpu"
        )

    return _model


def generate_embeddings(chunks):
    """
    Generate embeddings for text chunks.
    """

    model = get_model()

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

    model = get_model()

    return model.encode(query).tolist()