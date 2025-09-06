from __future__ import annotations
from fastapi import FastAPI
from .routers import ingest, qa, docs, history

app = FastAPI(title="API Doc Answerer + Snippet Generator")

app.include_router(ingest.router)
app.include_router(qa.router)
app.include_router(docs.router)
app.include_router(history.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
