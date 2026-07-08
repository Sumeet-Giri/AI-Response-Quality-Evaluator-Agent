# Agent Design

## Multi-Agent Architecture

The system follows a modular multi-agent architecture.

---

## Input Validation Agent

Responsibilities:

- Validate inputs
- Check required fields
- Verify uploaded documents

Output:

- Clean evaluation request

---

## Retrieval Agent

Responsibilities:

- Query vector database
- Retrieve supporting context
- Return relevant chunks

Output:

- Retrieved evidence

---

## Relevance Agent

Responsibilities:

- Measure alignment between question and answer
- Detect off-topic responses

Output:

- Relevance score

---

## Hallucination Agent

Responsibilities:

- Compare claims with retrieved evidence
- Identify unsupported statements

Output:

- Hallucination score

---

## Similarity Agent

Responsibilities:

- Compare AI response with reference answer

Metrics:

- Cosine Similarity
- Semantic Similarity

Output:

- Similarity score

---

## Aggregation Agent

Responsibilities:

- Combine scores
- Generate final evaluation report

Output:

- Overall quality score
