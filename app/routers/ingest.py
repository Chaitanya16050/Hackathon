from __future__ import annotations
from fastapi import APIRouter, UploadFile, File
from typing import List
from bson import ObjectId
from ..db import docs_col, chunks_col
from ..utils.text import chunk_text, clean_markdown
from ..services.qa import index_doc
from ..utils.serialize import to_serializable
import yaml

router = APIRouter()


def _detect_type(name: str, content: str) -> str:
    lower = name.lower()
    if lower.endswith((".yaml", ".yml")):
        try:
            y = yaml.safe_load(content)
            if isinstance(y, dict) and ("openapi" in y or "swagger" in y):
                return "openapi"
        except Exception:
            pass
    if lower.endswith((".json",)):
        try:
            import json
            j = json.loads(content)
            if isinstance(j, dict) and ("openapi" in j or "swagger" in j):
                return "openapi"
        except Exception:
            pass
    return "markdown"


@router.post("/ingest")
async def ingest(files: List[UploadFile] = File(...)):
    doc_ids: List[str] = []
    total_chunks = 0
    for f in files:
        raw = (await f.read()).decode("utf-8", errors="ignore")
        doc_type = _detect_type(f.filename, raw)
        content = raw if doc_type == "openapi" else clean_markdown(raw)
        doc = {"name": f.filename, "type": doc_type, "content": content}
        inserted = docs_col.insert_one(doc)
        _id = inserted.inserted_id
        doc_ids.append(str(_id))

        # chunk content
        if doc_type == "openapi":
            # put whole content as one chunk and minimal path-level chunks
            chunks = [{"_id": ObjectId(), "doc_id": _id, "text": content, "fragment": "spec"}]
            try:
                y = yaml.safe_load(content) or {}
                for p in (y.get("paths", {}) or {}).keys():
                    chunks.append({"_id": ObjectId(), "doc_id": _id, "text": f"Path: {p}", "fragment": p})
            except Exception:
                pass
        else:
            texts = chunk_text(content)
            chunks = [
                {"_id": ObjectId(), "doc_id": _id, "text": t, "fragment": f"md:{i}"}
                for i, t in enumerate(texts)
            ]
        if chunks:
            chunks_col.insert_many(chunks)
            total_chunks += len(chunks)
            # index
            index_doc({"_id": _id}, chunks)
    return to_serializable({"doc_ids": doc_ids, "chunks_indexed": total_chunks})
