from __future__ import annotations
from typing import List, Dict, Any, Tuple
from ..config import settings

try:
    from pinecone import Pinecone  # type: ignore
except Exception:  # pragma: no cover
    Pinecone = None  # type: ignore


class MemoryVectorStore:
    def __init__(self):
        self.vectors: List[Tuple[str, list[float], Dict[str, Any]]] = []

    def upsert(self, items: List[Tuple[str, list[float], Dict[str, Any]]]):
        self.vectors.extend(items)

    def delete(self, filter_meta: Dict[str, Any]):
        doc_id = filter_meta.get("doc_id")
        if doc_id is None:
            return
        self.vectors = [v for v in self.vectors if v[2].get("doc_id") != doc_id]

    def query(self, emb: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        import numpy as np
        if not self.vectors:
            return []
        v = np.array(emb)
        sims = []
        for _id, vec, meta in self.vectors:
            arr = np.array(vec)
            denom = (np.linalg.norm(v) * np.linalg.norm(arr)) or 1.0
            sim = float(v.dot(arr) / denom)
            sims.append((sim, _id, meta))
        sims.sort(reverse=True)
        results: List[Dict[str, Any]] = []
        for sim, _id, meta in sims[:top_k]:
            item = {"id": _id, "score": sim, "metadata": meta}
            results.append(item)
        return results


class PineconeVectorStore:
    def __init__(self):
        assert Pinecone is not None, "pinecone client not installed"
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        # ensure index
        try:
            self.index = self.pc.Index(settings.pinecone_index)
        except Exception:
            # create index if it doesn't exist
            self.pc.create_index(
                name=settings.pinecone_index,
                dimension=384,
                metric="cosine",
                spec={"serverless": {"cloud": settings.pinecone_cloud, "region": settings.pinecone_region}},
            )
            self.index = self.pc.Index(settings.pinecone_index)

    def upsert(self, items: List[Tuple[str, list[float], Dict[str, Any]]]):
        vectors = [
            {
                "id": _id,
                "values": vec,
                "metadata": meta,
            }
            for _id, vec, meta in items
        ]
        self.index.upsert(vectors=vectors)

    def delete(self, filter_meta: Dict[str, Any]):
        doc_id = filter_meta.get("doc_id")
        if doc_id is None:
            return
        self.index.delete(filter={"doc_id": {"$eq": doc_id}})

    def query(self, emb: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        res = self.index.query(vector=emb, top_k=top_k, include_metadata=True)
        return [
            {"id": m.get("id") if isinstance(m, dict) else m.id, "score": m.get("score") if isinstance(m, dict) else m.score, "metadata": m.get("metadata") if isinstance(m, dict) else m.metadata}
            for m in res.get("matches", [])
        ]


def get_vectorstore():
    if settings.use_memory_vectorstore or not settings.pinecone_api_key or Pinecone is None:
        return MemoryVectorStore()
    return PineconeVectorStore()
