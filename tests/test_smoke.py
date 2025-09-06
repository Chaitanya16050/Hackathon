import os
os.environ.setdefault("USE_MEMORY_VECTORSTORE", "1")
os.environ.setdefault("USE_FAKE_EMBEDDINGS", "1")
os.environ.setdefault("USE_MOCK_DB", "1")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_smoke_ingest_qa_history(tmp_path):
    # ingest sample docs
    openapi_file = ("openapi.yaml", open("sample_docs/openapi.yaml", "rb"), "application/yaml")
    md_file = ("guide.md", open("sample_docs/guide.md", "rb"), "text/markdown")
    resp = client.post("/ingest", files=[("files", openapi_file), ("files", md_file)])
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["doc_ids"]) >= 2

    # ask a question
    q = {"question": "How do I create an invoice?"}
    resp = client.post("/qa", json=q)
    assert resp.status_code == 200, resp.text
    qa = resp.json()
    assert qa.get("answer") and len(qa.get("answer")) > 0
    assert len(qa.get("citations", [])) >= 2
    assert len(qa.get("snippets", [])) >= 2

    # history
    resp = client.get("/history")
    assert resp.status_code == 200
    items = resp.json()
    assert any(i.get("question") == q["question"] for i in items)

    # retrieve first item
    qa_id = qa.get("id")
    if qa_id:
        resp = client.get(f"/history/{qa_id}")
        assert resp.status_code == 200
