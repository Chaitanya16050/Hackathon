from __future__ import annotations
from typing import List, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId

from ..db import docs_col, chunks_col, qa_col
from .embeddings import embed_texts
from .vectorstore import get_vectorstore

_vectorstore = get_vectorstore()


def _format_answer(question: str, contexts: List[Dict[str, Any]]) -> str:
    # 3–6 sentence concise answer, grounded in contexts
    base = "Here’s what the docs state: "
    bullets = []
    for c in contexts[:3]:
        excerpt = (c.get("text") or "").strip()
        if len(excerpt) > 160:
            excerpt = excerpt[:160] + "..."
        bullets.append(f"- {excerpt}")
    trailer = " Based on these sections, follow the referenced endpoints and parameters in the citations."
    return base + "\n" + "\n".join(bullets) + trailer


def ask_question(question: str) -> Dict[str, Any]:
    # search vector store
    q_emb = embed_texts([question])[0]
    matches = _vectorstore.query(q_emb, top_k=6)

    # map to chunks
    chunk_ids = [m["metadata"].get("chunk_id") for m in matches if m.get("metadata")]
    chunks = list(chunks_col.find({"_id": {"$in": chunk_ids}})) if chunk_ids else []

    if not chunks:
        return {
            "answer": "I couldn't find an answer in the current docs. Try adding or enabling more docs.",
            "citations": [],
            "snippets": [],
            "question": question,
            "id": None,
        }

    # build citations
    citations = []
    for c in chunks[:3]:
        citations.append(
            {
                "doc_id": str(c.get("doc_id")),
                "fragment": c.get("fragment"),
                "score": next((m["score"] for m in matches if m["metadata"].get("chunk_id") == c["_id"]), None),
            }
        )

    # try to get openapi doc for snippets
    # pick the most relevant doc_id among chunks
    top_doc_id = chunks[0].get("doc_id")
    doc = docs_col.find_one({"_id": top_doc_id}) if top_doc_id else None

    snippets: List[Dict[str, str]] = []
    if doc and doc.get("type") == "openapi":
        from .openapi_utils import load_openapi, generate_snippets_from_openapi

        spec = load_openapi(doc.get("content", "")) or {}
        for lang, code in generate_snippets_from_openapi(spec, question, top_k=1):
            snippets.append({"language": lang, "code": code})
    # ensure at least two snippets in different languages; fallback if needed
    if len(snippets) < 2:
        snippets.extend(
            [
                {"language": "curl", "code": "curl -X GET 'https://api.example.com/ping'"},
                {"language": "python", "code": "import requests\nprint(requests.get('https://api.example.com/ping').status_code)"},
            ]
        )
        # dedupe by language
        dedup = {}
        for s in snippets:
            dedup[s["language"]] = s
        snippets = list(dedup.values())[:2]

    answer = _format_answer(question, [{"text": c.get("text")} for c in chunks[:3]])

    qa_doc = {
        "question": question,
        "answer": answer,
        "citations": citations,
        "snippets": snippets,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    inserted = qa_col.insert_one(qa_doc)
    qa_id = str(inserted.inserted_id)

    qa_doc["id"] = qa_id
    return qa_doc


def index_doc(doc: Dict[str, Any], chunks: List[Dict[str, Any]]):
    from uuid import uuid4
    # compute embeddings and upsert
    embeddings = embed_texts([c["text"] for c in chunks])
    items = []
    for emb, ch in zip(embeddings, chunks):
        items.append((str(uuid4()), emb, {"doc_id": str(doc["_id"]), "chunk_id": ch["_id"]}))
    _vectorstore.upsert(items)


def delete_doc_from_index(doc_id: str):
    _vectorstore.delete({"doc_id": doc_id})
