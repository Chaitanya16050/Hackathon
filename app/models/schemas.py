from __future__ import annotations
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

class IngestResponse(BaseModel):
    doc_ids: List[str]
    chunks_indexed: int

class QARequest(BaseModel):
    question: str

class Citation(BaseModel):
    doc_id: str
    fragment: Optional[str] = None
    score: Optional[float] = None

class Snippet(BaseModel):
    language: Literal["curl", "python", "javascript", "typescript"]
    code: str

class QAResponse(BaseModel):
    id: str
    question: str
    answer: str
    citations: List[Citation]
    snippets: List[Snippet]

class QAListItem(BaseModel):
    id: str
    question: str
    created_at: str

class DocInfo(BaseModel):
    id: str
    name: str
    type: Literal["openapi", "markdown"]
    created_at: str
