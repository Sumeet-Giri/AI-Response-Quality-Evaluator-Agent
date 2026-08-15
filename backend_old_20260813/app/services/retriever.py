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


def retrieve_reference(query: str, top_k: int = 1, max_distance: float = 0.75):
    """
    Resilient single-best-passage retrieval for the evaluation orchestrator.

    Returns {"text": ..., "metadata": ..., "distance": ...} for the top
    hit, or None if nothing USEFUL could be retrieved.

    "Useful" is gated by max_distance: with the collection configured for
    cosine distance (see chroma_manager.py), distance = 1 - cosine
    similarity, so a distance of 0.75 corresponds to only ~0.25 cosine
    similarity -- i.e. barely related at all. Below that bar, the closest
    match in the knowledge base still isn't a real match; it's just the
    least-bad option among everything stored. Handing that back as
    "reference evidence" is worse than having no reference at all, because
    Accuracy/Hallucination would then score the response against text
    that has nothing to do with the question, producing a confidently
    wrong-looking 0 instead of an honest "no evidence available."

    This threshold is intentionally permissive (not stringent) -- it's
    only meant to catch the "completely unrelated topic" case (e.g. an
    arithmetic or acronym question retrieving a passage about Lourdes),
    not to second-guess genuinely close-but-imperfect matches.

    None is also returned, as before, when the knowledge base hasn't been
    seeded yet or the retrieval layer errors for any reason.
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

    top_distance = distances[0] if distances else None
    if top_distance is not None and top_distance > max_distance:
        return None

    return {
        "text": documents[0],
        "metadata": metadatas[0] if metadatas else {},
        "distance": top_distance,
    }
