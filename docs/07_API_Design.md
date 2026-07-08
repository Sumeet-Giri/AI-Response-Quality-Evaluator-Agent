# API Design

## Base URL

```text
http://localhost:8000
```

---

# Evaluate Response

## Endpoint

```http
POST /evaluate
```

---

## Request

```json
{
  "question": "What is AI?",
  "ai_response": "Artificial Intelligence is...",
  "reference_answer": "Artificial Intelligence refers to..."
}
```

---

## Response

```json
{
  "overall_score": 8.5,
  "relevance_score": 9.1,
  "hallucination_score": 8.0,
  "similarity_score": 8.4,
  "feedback": "Response is relevant with minor unsupported claims."
}
```

---

# Health Check

## Endpoint

```http
GET /health
```

Response:

```json
{
  "status": "healthy"
}
```

---

# Future APIs

- POST /upload-document
- GET /evaluation-history
- GET /report/{id}
