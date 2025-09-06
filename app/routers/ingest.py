from __future__ import annotations
from fastapi import APIRouter, UploadFile, File
from fastapi import HTTPException
from typing import List
from bson import ObjectId
from ..db import docs_col, chunks_col
from ..utils.text import chunk_text, clean_markdown
from ..services.qa import index_doc
from ..utils.serialize import to_serializable
import yaml
import json

router = APIRouter()


def _detect_type_json_only(name: str, content: str) -> str:
    lower = name.lower()
    if not lower.endswith(".json"):
        raise HTTPException(status_code=400, detail=f"Only JSON is supported. Invalid file: {name}")
    try:
        j = json.loads(content)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid JSON content: {name}")
    if isinstance(j, dict) and ("openapi" in j or "swagger" in j):
        return "openapi"
    # If not an OpenAPI JSON, reject
    raise HTTPException(status_code=400, detail=f"Unsupported JSON type (expect OpenAPI): {name}")


@router.post("/ingest")
async def ingest(files: List[UploadFile] = File(...)):
    doc_ids: List[str] = []
    total_chunks = 0
    for f in files:
        raw = (await f.read()).decode("utf-8", errors="ignore")
        doc_type = _detect_type_json_only(f.filename, raw)
        content = raw
        doc = {"name": f.filename, "type": doc_type, "content": content}
        inserted = docs_col.insert_one(doc)
        _id = inserted.inserted_id
        doc_ids.append(str(_id))

        # chunk content
        # OpenAPI JSON: put whole content as one chunk and minimal path-level chunks
        chunks = [{"_id": ObjectId(), "doc_id": _id, "text": content, "fragment": "spec"}]
        try:
            j = json.loads(content) or {}
            for p in (j.get("paths", {}) or {}).keys():
                chunks.append({"_id": ObjectId(), "doc_id": _id, "text": f"Path: {p}", "fragment": p})
        except Exception:
            pass
        if chunks:
            chunks_col.insert_many(chunks)
            total_chunks += len(chunks)
            # index
            index_doc({"_id": _id}, chunks)
    return to_serializable({"doc_ids": doc_ids, "chunks_indexed": total_chunks})
