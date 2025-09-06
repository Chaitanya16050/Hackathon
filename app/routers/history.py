from __future__ import annotations
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from ..db import qa_col
from ..utils.serialize import to_serializable

router = APIRouter()


@router.get("/history")
async def list_history():
    items = []
    for q in qa_col.find().sort("_id", -1).limit(50):
        items.append({"id": str(q["_id"]), "question": q.get("question"), "created_at": q.get("created_at")})
    return to_serializable(items)


@router.get("/history/{qa_id}")
async def get_history(qa_id: str):
    try:
        _id = ObjectId(qa_id)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid id")
    q = qa_col.find_one({"_id": _id})
    if not q:
        raise HTTPException(status_code=404, detail="not found")
    q["id"] = str(q["_id"])
    del q["_id"]
    return to_serializable(q)
