import chromadb
import uuid

# NOTE: this module is now on the LIVE request path -- app.services.retriever
# (imported lazily by the EvaluationOrchestrator's RAG fallback) depends on
# `collection` below. Previously this file was only ever imported by opt-in
# manual scripts. The collection starts empty on a fresh checkout; run
# `python scripts/test_chromadb.py` once to seed it from TruthfulQA/SQuAD
# before RAG fallback has anything to retrieve. Until then, RAG fallback
# degrades gracefully to "no reference available" (see retriever.py) rather
# than failing -- so this is a "does more with a seeded KB" component, not a
# hard runtime requirement.

# Create/Open a persistent database
client = chromadb.PersistentClient(path="chroma_db")

# Create or load a collection
collection = client.get_or_create_collection(
    name="reference_knowledge_base"
)


def store_embeddings(embedded_chunks):
    """
    Store embedded chunks into ChromaDB.
    """

    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for index, chunk in enumerate(embedded_chunks):

        ids.append(str(uuid.uuid4()))

        documents.append(chunk["text"])

        embeddings.append(chunk["embedding"])

        metadatas.append(chunk["metadata"])

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return collection.count()