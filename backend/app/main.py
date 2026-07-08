from fastapi import FastAPI  # type: ignore[import]

app = FastAPI(
    title="AI Response Quality Evaluator",
    version="1.0.0",
    description="Milestone 1 Prototype"
)


@app.get("/")
def home():
    return {
        "message": "AI Response Quality Evaluator API is running."
    }