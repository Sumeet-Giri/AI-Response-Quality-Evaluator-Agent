"""
Retriever
---------
Queries the reference knowledge base (ChromaDB, seeded from TruthfulQA /
SQuAD via scripts/test_chromadb.py) for passages relevant to a query.

`retrieve()` is the original low-level function (unchanged in behavior)
used directly by scripts/test_retriever.py for manual inspection.

`retrieve_reference()` is a new, resilient convenience wrapper built
specifically for the EvaluationOrchestrator's live RAG fallback. It:
  - imports chromadb lazily (inside the function, not at module load time)
    so that a Chroma/environment problem surfaces as "no evidence for this
    one request" instead of crashing the entire API at startup -- this
    matters now that retrieval sits on the live /evaluate/all request path,
    not just in an opt-in test script.
  - returns None instead of raising when the knowledge base is empty,
    unseeded, or unreachable, so callers can degrade gracefully.
"""


def retrieve(query, top_k=3):
    """
    Retrieve the top_k most relevant chunks from ChromaDB.
    Original low-level function, unchanged -- still used directly by
    scripts/test_retriever.py.
    """
    from app.services.embedder import generate_query_embedding
    from app.services.chroma_manager import collection

    query_embedding = generate_query_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    return results


def retrieve_reference(query: str, top_k: int = 1):
    """
    Resilient single-best-passage retrieval for the evaluation orchestrator.

    Returns {"text": ..., "metadata": ..., "distance": ...} for the top
    hit, or None if nothing could be retrieved -- whether because the
    knowledge base hasn't been seeded yet (see scripts/test_chromadb.py),
    because it's genuinely empty for this query, or because of any
    underlying retrieval-layer error (e.g. ChromaDB unavailable). Callers
    should always treat None as "no evidence available" and continue
    rather than fail the request.
    """
    try:
        results = retrieve(query, top_k=top_k)
    except Exception:
        # Deliberately broad: this is a best-effort fallback, not a
        # required dependency of evaluation. Any failure here (missing
        # package, empty/uninitialized collection, disk/permission issue)
        # should degrade to "no reference available", never take down a
        # live evaluation request.
        return None

    if not results:
        return None

    documents = results.get("documents") or [[]]
    documents = documents[0] if documents else []
    if not documents:
        return None

    metadatas = results.get("metadatas") or [[{}]]
    metadatas = metadatas[0] if metadatas else [{}]

    distances = results.get("distances") or [[None]]
    distances = distances[0] if distances else [None]

    return {
        "text": documents[0],
        "metadata": metadatas[0] if metadatas else {},
        "distance": distances[0] if distances else None,
    }
