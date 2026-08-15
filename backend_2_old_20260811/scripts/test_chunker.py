import sys
from pathlib import Path
# So this script works when run directly (python scripts/xxx.py) from ANY
# working directory, not just when backend/ happens to already be on
# sys.path (which is what pytest does automatically, but a plain `python`
# invocation does not -- it only adds the script's own folder).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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