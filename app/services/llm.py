from __future__ import annotations
from typing import Optional
from ..config import settings

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

try:
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover
    genai = None  # type: ignore


def generate_text(prompt: str, system: Optional[str] = None, max_tokens: int = 800) -> str:
    # Fake/offline fallback
    if getattr(settings, "use_fake_embeddings", False) and not settings.openai_api_key and not settings.gemini_api_key:
        # simple echo-ish deterministic content
        return "{\n\"snippets\": [\n{\"language\": \"curl\", \"code\": \"curl -X POST https://api.example.com/invoices -H 'Content-Type: application/json' -d {}\"},\n{\"language\": \"python\", \"code\": \"import requests\\nrequests.post('https://api.example.com/invoices', json={})\"}\n]\n}"

    provider = (settings.embeddings_provider or "").lower()

    if provider == "gemini" and settings.gemini_api_key and genai is not None:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")  # type: ignore
        parts = []
        if system:
            parts.append({"text": system})
        parts.append({"text": prompt})
        resp = model.generate_content(parts)  # type: ignore
        return resp.text or ""

    # default to OpenAI
    if settings.openai_api_key and OpenAI is not None:
        client = OpenAI(api_key=settings.openai_api_key)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        chat = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return chat.choices[0].message.content or ""

    # ultimate fallback
    return "{\n\"snippets\": [\n{\"language\": \"curl\", \"code\": \"curl -X GET https://api.example.com/ping\"},\n{\"language\": \"python\", \"code\": \"import requests\\nprint(requests.get('https://api.example.com/ping').status_code)\"}\n]\n}"
