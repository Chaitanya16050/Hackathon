from __future__ import annotations
from typing import List
import numpy as np
from ..config import settings

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

try:
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover
    genai = None  # type: ignore

_rng = np.random.default_rng(12345)


def _fake(texts: List[str]) -> List[List[float]]:
    return [(_rng.random(384) - 0.5).tolist() for _ in texts]


def _openai(texts: List[str]) -> List[List[float]]:
    if not settings.openai_api_key or OpenAI is None:
        return _fake(texts)
    client = OpenAI(api_key=settings.openai_api_key)
    resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
    return [d.embedding for d in resp.data]


def _gemini(texts: List[str]) -> List[List[float]]:
    if not settings.gemini_api_key or genai is None:
        return _fake(texts)
    genai.configure(api_key=settings.gemini_api_key)
    # Gemini embedding models: 'text-embedding-004' returns 768-d vectors
    model = genai.GenerativeModel("text-embedding-004")  # type: ignore
    out: List[List[float]] = []
    # batch one by one for simplicity
    for t in texts:
        try:
            r = genai.embed_content(model="text-embedding-004", content=t)  # type: ignore
            vec = r.get("embedding") if isinstance(r, dict) else getattr(r, "embedding", None)
            if vec is None:
                out.append(_rng.random(768).tolist())
            else:
                out.append(vec)
        except Exception:
            out.append(_rng.random(768).tolist())
    # if dim != 384, project/truncate to 384 to match index
    projected: List[List[float]] = []
    for v in out:
        if len(v) == 384:
            projected.append(v)
        elif len(v) > 384:
            projected.append(v[:384])
        else:
            # pad with zeros
            projected.append(v + [0.0] * (384 - len(v)))
    return projected


def embed_texts(texts: List[str]) -> List[List[float]]:
    if settings.use_fake_embeddings:
        return _fake(texts)
    provider = (settings.embeddings_provider or "").lower()
    if provider == "gemini":
        return _gemini(texts)
    # default to openai
    return _openai(texts)
