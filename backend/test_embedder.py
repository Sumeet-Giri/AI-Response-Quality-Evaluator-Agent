from app.services.dataset_loader import load_datasets
from app.services.chunker import create_chunks
from app.services.embedder import generate_embeddings

records = load_datasets(
    truthfulqa_limit=2,
    squad_limit=2
)

chunks = create_chunks(records)

embedded_chunks = generate_embeddings(chunks)

print("=" * 60)
print(f"Total Embedded Chunks: {len(embedded_chunks)}")
print("=" * 60)

print()

print("Dataset:", embedded_chunks[0]["metadata"]["dataset"])

print()

print("Embedding Length:", len(embedded_chunks[0]["embedding"]))

print()

print("First 10 Values:")

print(embedded_chunks[0]["embedding"][:10])