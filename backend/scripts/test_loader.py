import sys
from pathlib import Path
# So this script works when run directly (python scripts/xxx.py) from ANY
# working directory, not just when backend/ happens to already be on
# sys.path (which is what pytest does automatically, but a plain `python`
# invocation does not -- it only adds the script's own folder).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.dataset_loader import load_datasets

data = load_datasets(
    truthfulqa_limit=2,
    squad_limit=2
)

print("=" * 60)
print(f"Total Records : {len(data)}")
print("=" * 60)

for i, record in enumerate(data, start=1):
    print(f"\nRecord {i}")
    print("-" * 40)

    print("Dataset :", record["dataset"])
    print("Question:", record["question"])
    print("Answer  :", record["answer"])

    if record["context"]:
        print("Context :", record["context"][:100], "...")

    print("Source  :", record["source"])