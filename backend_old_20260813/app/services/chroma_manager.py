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

# Create or load a collection.
# hnsw:space is set explicitly to "cosine" rather than relying on ChromaDB's
# default (squared L2) -- cosine distance is bounded and directly comparable
# to the similarity scale the rest of this codebase already uses (e.g.
# relevance_agent's 0.50 topic-match cutoff), which is what
# retriever.retrieve_reference()'s relevance threshold depends on below.
#
# NOTE: this setting only applies when the collection is first CREATED.
# If you seeded chroma_db/ before this change, delete that folder and
# re-run scripts/test_chromadb.py so the collection is recreated with
# cosine distance -- get_or_create_collection will not retroactively
# change the distance space of an existing collection.
collection = client.get_or_create_collection(
    name="reference_knowledge_base",
    metadata={"hnsw:space": "cosine"}
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