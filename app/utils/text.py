from __future__ import annotations
import re
from typing import Iterable, List

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def chunk_text(text: str, max_len: int = 1200, overlap: int = 200) -> List[str]:
    if not text:
        return []
    sentences = re.split(SENTENCE_SPLIT, text)
    chunks: List[str] = []
    cur: List[str] = []
    cur_len = 0
    for s in sentences:
        s_len = len(s)
        if cur_len + s_len > max_len and cur:
            chunks.append(" ".join(cur))
            # start new chunk with overlap
            if overlap > 0 and chunks[-1]:
                tail = chunks[-1][-overlap:]
                cur = [tail]
                cur_len = len(tail)
            else:
                cur = []
                cur_len = 0
        cur.append(s)
        cur_len += s_len + 1
    if cur:
        chunks.append(" ".join(cur))
    return [c.strip() for c in chunks if c.strip()]


def clean_markdown(md: str) -> str:
    return md.replace("\r\n", "\n").strip()
