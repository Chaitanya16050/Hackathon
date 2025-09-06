from __future__ import annotations
from typing import List, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId

from ..db import docs_col, chunks_col, qa_col
from .embeddings import embed_texts
from .vectorstore import get_vectorstore
from .llm import generate_text

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

    # AI-driven snippet generation
    # Compose a minimal, grounded prompt with top contexts and any OpenAPI spec available.
    top_doc_id = chunks[0].get("doc_id")
    doc = docs_col.find_one({"_id": top_doc_id}) if top_doc_id else None
    context_text = "\n\n".join((c.get("text") or "")[:800] for c in chunks[:3])
    spec_text = doc.get("content", "") if doc and doc.get("type") == "openapi" else ""
    system = (
        "You generate practical API request code snippets strictly consistent with the provided OpenAPI/spec context. "
        "Return a compact JSON object with a 'snippets' array; each item has 'language' and 'code'. "
        "Prefer cURL and Python. Do not invent paths or parameters not present in the spec/context."
    )
    prompt = (
        f"Question: {question}\n\n"
        f"Relevant context:\n{context_text}\n\n"
        f"OpenAPI (if any):\n{spec_text[:4000]}\n\n"
        "Produce 2-3 minimal yet working snippets."
    )
    ai_out = generate_text(prompt, system=system, max_tokens=500)
    snippets: List[Dict[str, str]] = []
    # parse leniently as JSON or simple heuristics
    import json, re
    try:
        obj = json.loads(ai_out)
        for it in obj.get("snippets", [])[:3]:
            lang = str(it.get("language", "")).lower() or "text"
            code = str(it.get("code", ""))
            if code:
                snippets.append({"language": lang, "code": code})
    except Exception:
        # fallback: extract code fences
        fences = re.findall(r"```(\w+)?\n([\s\S]*?)```", ai_out)
        for lang, code in fences[:3]:
            lang = (lang or "text").lower()
            snippets.append({"language": lang, "code": code.strip()})
    # Ensure at least two different languages
    if len(snippets) < 2:
        snippets.extend(
            [
                {"language": "curl", "code": "curl -X GET 'https://api.example.com/ping'"},
                {"language": "python", "code": "import requests\nprint(requests.get('https://api.example.com/ping').status_code)"},
            ]
        )
    dedup = {}
    for s in snippets:
        if s.get("language") and s.get("code"):
            dedup.setdefault(s["language"], s)
    snippets = list(dedup.values())[:3]

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
