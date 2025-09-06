# API Doc Answerer + Snippet Generator (FastAPI + MongoDB + Pinecone)

This backend ingests a tiny set of product/API docs (OpenAPI and/or Markdown), answers user questions with grounded citations, and generates code snippets in multiple languages. Q&A are persisted and can be revisited from history.

## Features

- Ingest OpenAPI (YAML/JSON) and Markdown docs
- Vector search over content (Pinecone or in-memory fallback)
- Answer questions with 3–6 sentence grounded responses and clickable citations
- Generate 2+ code snippets per query (e.g., cURL + Python) from OpenAPI
- Persist docs and Q&A history in MongoDB
- Delete docs and have retrieval update accordingly
- Smoke test covering ingest → ask → answer with ≥2 citations and 2 snippets → history saved

## Tech Stack

- FastAPI
- MongoDB (pymongo)
- Pinecone (vector DB). Fallback to in-memory vector store for local/dev without keys.
- OpenAI embeddings by default; optional fake embeddings for offline tests

## Quickstart

1) Environment

Create a `.env` file in the project root:

```
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=aidenai
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX=aidenai-docs
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
OPENAI_API_KEY=your_openai_key
# For offline/local smoke tests without external services:
USE_FAKE_EMBEDDINGS=0
USE_MEMORY_VECTORSTORE=0
```

2) Install

```
# Windows PowerShell
python -m venv .venv; .\.venv\\Scripts\\Activate.ps1; python -m pip install -U pip; pip install -r requirements.txt
```

3) Run the API

```
uvicorn app.main:app --reload --port 8000
```

4) Try the demo

- Ingest sample docs:
  - POST http://localhost:8000/ingest with multipart files from `sample_docs/` (e.g., `openapi.yaml` and `guide.md`).
- Ask a question: POST http://localhost:8000/qa with JSON `{ "question": "How do I create an invoice?" }`.
- See history: GET http://localhost:8000/history
- Open a past Q&A: GET http://localhost:8000/history/{id}
- List/Delete docs: GET/DELETE http://localhost:8000/docs

## Endpoints

- POST /ingest — Upload OpenAPI/Markdown docs. Indexes chunks into Pinecone (or memory) and stores metadata in MongoDB.
- GET /docs — List docs and status.
- DELETE /docs/{doc_id} — Remove doc, de-index from vector store.
- POST /qa — Ask a question. Returns an answer with citations and code snippets. Saves to history.
- GET /history — List past queries.
- GET /history/{qa_id} — Retrieve a previous Q&A.
- GET /health — Liveness check.

## Testing

Offline smoke test (uses memory vector store + fake embeddings):

```
$env:USE_MEMORY_VECTORSTORE = "1"; $env:USE_FAKE_EMBEDDINGS = "1"; pytest -q
```

## Notes

- If no Pinecone or OpenAI keys are provided, the service will use an in-memory vector store and fake embeddings to enable local dev and tests.
- Citations include doc ID and section anchors; frontend can make them clickable to the ingested doc fragment.

## License

MIT
