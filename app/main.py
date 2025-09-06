from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import ingest, qa, docs, history

app = FastAPI(title="API Doc Answerer + Snippet Generator")

origins = [o.strip() for o in (settings.cors_allow_origins or "*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"]
    ,
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

app.include_router(ingest.router)
app.include_router(qa.router)
app.include_router(docs.router)
app.include_router(history.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
