from app.services.dataset_loader import load_datasets
from app.services.chunker import create_chunks
from app.services.embedder import generate_embeddings
from app.services.chroma_manager import store_embeddings

records = load_datasets(
    truthfulqa_limit=2,
    squad_limit=2
)

chunks = create_chunks(records)

embedded_chunks = generate_embeddings(chunks)

count = store_embeddings(embedded_chunks)

print("=" * 60)
print(f"Documents Stored : {count}")
print("=" * 60)