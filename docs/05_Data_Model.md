# Data Model

## Evaluation Request

```json
{
  "question": "string",
  "ai_response": "string",
  "reference_answer": "string",
  "source_document": "file"
}
```

---

## Evaluation Result

```json
{
  "relevance_score": 0.0,
  "faithfulness_score": 0.0,
  "hallucination_score": 0.0,
  "similarity_score": 0.0,
  "overall_score": 0.0,
  "feedback": "string"
}
```

---

## Knowledge Base Record

```json
{
  "id": "string",
  "source": "TruthfulQA",
  "question": "string",
  "answer": "string",
  "embedding": []
}
```
