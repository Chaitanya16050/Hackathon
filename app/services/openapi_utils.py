from __future__ import annotations
from typing import Any, Dict, List, Tuple
import yaml


def load_openapi(content: str) -> Dict[str, Any]:
    return yaml.safe_load(content)


def find_paths_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    return spec.get("paths", {})


def generate_snippets_from_openapi(
    spec: Dict[str, Any],
    question: str,
    top_k: int = 2,
) -> List[Tuple[str, str]]:
    # naive heuristic: search operationId/summary/description for keywords
    q = question.lower()
    matches: List[Tuple[float, str, str]] = []
    for path, methods in find_paths_spec(spec).items():
        for method, op in methods.items():
            text = " ".join([
                str(op.get("operationId", "")),
                str(op.get("summary", "")),
                str(op.get("description", "")),
            ]).lower()
            score = sum(1 for token in q.split() if token in text)
            # prefer create-like actions
            if any(k in text for k in ["create", "add", "new"]):
                score += 2
            if score > 0:
                matches.append((float(score), method.upper(), path))
    matches.sort(reverse=True)
    snippets: List[Tuple[str, str]] = []
    for _score, method, path in matches[:top_k]:
        # Minimal examples without auth headers; frontend can augment
        curl = f"curl -X {method} 'https://api.example.com{path}' -H 'Content-Type: application/json' -d '{{}}'"
        py = (
            "import requests\n"
            f"resp = requests.request('{method}', 'https://api.example.com{path}', json={{}})\n"
            "print(resp.status_code, resp.text)\n"
        )
        snippets.append(("curl", curl))
        snippets.append(("python", py))
    return snippets
