from app.services.embedder import generate_query_embedding
from app.services.chroma_manager import collection


def retrieve(query, top_k=3):
    """
    Retrieve the most relevant chunks from ChromaDB.
    """

    query_embedding = generate_query_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    return results