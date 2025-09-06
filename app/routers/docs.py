from __future__ import annotations
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from ..db import docs_col, chunks_col
from ..services.qa import delete_doc_from_index
from ..utils.serialize import to_serializable

router = APIRouter()


@router.get("/docs")
async def list_docs():
    docs = []
    for d in docs_col.find():
        docs.append({"id": str(d["_id"]), "name": d.get("name"), "type": d.get("type"), "created_at": str(d.get("_id").generation_time)})
    return to_serializable(docs)


@router.delete("/docs/{doc_id}")
async def delete_doc(doc_id: str):
    try:
        _id = ObjectId(doc_id)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid id")
    d = docs_col.find_one({"_id": _id})
    if not d:
        raise HTTPException(status_code=404, detail="not found")
    chunks_col.delete_many({"doc_id": _id})
    docs_col.delete_one({"_id": _id})
    delete_doc_from_index(doc_id)
    return to_serializable({"status": "deleted", "id": doc_id})
