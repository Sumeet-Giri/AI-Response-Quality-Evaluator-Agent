import sys
from pathlib import Path
# So this script works when run directly (python scripts/xxx.py) from ANY
# working directory, not just when backend/ happens to already be on
# sys.path (which is what pytest does automatically, but a plain `python`
# invocation does not -- it only adds the script's own folder).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.retriever import retrieve

query = "What happens if you swallow watermelon seeds?"

results = retrieve(query)

print("=" * 60)
print("Retrieved Documents")
print("=" * 60)

documents = results["documents"][0]
metadatas = results["metadatas"][0]
distances = results["distances"][0]

for i in range(len(documents)):

    print(f"\nResult {i+1}")
    print("-" * 40)

    print("Distance :", distances[i])
    print("Dataset  :", metadatas[i]["dataset"])
    print("Source   :", metadatas[i]["source"])

    print()

    print(documents[i][:400])

    print()