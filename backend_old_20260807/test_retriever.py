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