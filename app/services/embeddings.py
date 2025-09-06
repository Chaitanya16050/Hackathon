from __future__ import annotations
from typing import List
import numpy as np
from ..config import settings

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

_rng = np.random.default_rng(12345)


def embed_texts(texts: List[str]) -> List[List[float]]:
    if settings.use_fake_embeddings or not settings.openai_api_key or OpenAI is None:
        # deterministic fake embeddings for tests/dev
        return [(_rng.random(384) - 0.5).tolist() for _ in texts]
    client = OpenAI(api_key=settings.openai_api_key)
    # use small embedding model
    resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
    return [d.embedding for d in resp.data]
