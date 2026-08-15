from app.services.dataset_loader import load_datasets
from app.services.chunker import create_chunks

records = load_datasets(
    truthfulqa_limit=2,
    squad_limit=2
)

chunks = create_chunks(records)

print(f"Total Chunks: {len(chunks)}")

print()

print(chunks[0])

print()

print(chunks[-1])