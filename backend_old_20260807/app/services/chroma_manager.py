import chromadb
import uuid

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