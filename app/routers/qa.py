from __future__ import annotations
from fastapi import APIRouter
from ..models.schemas import QARequest
from ..utils.serialize import to_serializable
from ..services.qa import ask_question

router = APIRouter()


@router.post("/qa")
async def qa(req: QARequest):
    return to_serializable(ask_question(req.question))
