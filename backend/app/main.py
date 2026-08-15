import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api import evaluate
from app.api import validation
from app.api import history
from app.services import history_store


logger = logging.getLogger("evaluator")
logging.basicConfig(level=logging.INFO)


app = FastAPI(
    title="AI Response Quality Evaluator Agent"
)


@app.on_event("startup")
def _startup():
    # Idempotent -- safe to call on every process start, creates the
    # evaluation_history.db table/indexes if they don't already exist.
    history_store.init_db()


app.include_router(
    evaluate.router,
    prefix="/evaluate",
    tags=["Evaluation"]
)


app.include_router(
    validation.router,
    prefix="/validation",
    tags=["Validation"]
)


app.include_router(
    history.router,
    prefix="/history",
    tags=["History"]
)


# ---------------------------------------------------------------------
# Global error handling
# ---------------------------------------------------------------------
# Previously there were no exception handlers at all: any unhandled error
# inside an agent (or, now, inside the RAG fallback -- though that layer
# is already designed to degrade gracefully rather than raise) surfaced
# as FastAPI's default 500 response with a raw Python traceback in the
# body. These two handlers keep that same behavior for genuinely
# unexpected errors (still a 500, still logged with the full traceback
# server-side, for debugging) but return a clean, consistent JSON error
# shape to the caller instead of leaking internals.

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # This is what now fires for the empty-question/response case added
    # in app/schemas/request.py -- returns FastAPI's normal structured
    # 422 detail (which field failed and why), just via an explicit
    # handler so the shape is documented rather than incidental.
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "detail": jsonable_encoder(exc.errors())},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "detail": "Something went wrong while processing this request.",
        },
    )


@app.get("/health")
def health_check():
    """Lightweight liveness check -- useful for the frontend's demo-mode
    fallback and for anything standing this app up behind a process
    manager later."""
    return {"status": "ok"}
