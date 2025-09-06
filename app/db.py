from pymongo import MongoClient
from .config import settings
import os

USE_MOCK_DB = os.getenv("USE_MOCK_DB", "0") == "1"

if USE_MOCK_DB:
	try:
		import mongomock  # type: ignore
	except Exception:  # pragma: no cover
		mongomock = None  # type: ignore
	if mongomock is None:
		# fallback to real client if mongomock not available
		_client = MongoClient(settings.mongodb_uri)
	else:
		_client = mongomock.MongoClient()
else:
	_client = MongoClient(settings.mongodb_uri)

_db = _client[settings.mongodb_db]

docs_col = _db["docs"]
chunks_col = _db["doc_chunks"]
qa_col = _db["qa_history"]

__all__ = ["docs_col", "chunks_col", "qa_col"]
