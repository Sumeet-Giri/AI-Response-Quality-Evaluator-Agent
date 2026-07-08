from datasets import load_dataset

dataset = load_dataset(
    "truthfulqa/truthful_qa",
    "generation"
)

record = dataset["validation"][0]

print(record)