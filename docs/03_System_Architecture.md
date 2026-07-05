# System Architecture

## High-Level Architecture

```text
User
 │
 ▼
Evaluation Input Module
 │
 ▼
Evaluation Orchestrator
 │
 ├── Retrieval Agent
 ├── Relevance Agent
 ├── Hallucination Agent
 ├── Similarity Agent
 │
 ▼
Score Aggregator
 │
 ▼
Evaluation Report
```

---

## Components

### Evaluation Input Module

Responsible for collecting:

- Question
- AI Response
- Reference Answer
- Source Documents

---

### Evaluation Orchestrator

Coordinates all evaluation agents.

Responsibilities:

- Manage workflow
- Invoke agents
- Aggregate outputs

---

### Knowledge Base

Stores:

- TruthfulQA
- SQuAD
- Processed chunks
- Embeddings

---

### Evaluation Agents

Each agent evaluates a specific quality dimension.

---

### Score Aggregator

Combines individual scores into a final report.

---

## Architecture Goals

- Modularity
- Scalability
- Explainability
- Extensibility
