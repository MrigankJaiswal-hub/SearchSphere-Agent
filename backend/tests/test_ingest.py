# backend/tests/test_ingest.py
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_ingest_empty():
    r = client.post("/api/ingest", json={})
    assert r.status_code in (400, 422)  # requires content
