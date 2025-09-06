from __future__ import annotations
from typing import Any
from bson import ObjectId
from datetime import datetime


def to_serializable(obj: Any) -> Any:
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {str(k): to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_serializable(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(to_serializable(v) for v in obj)
    return obj
