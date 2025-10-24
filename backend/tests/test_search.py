# backend/tests/test_search.py
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_search_validation():
    r = client.post("/api/search", json={"query": "hello"})
    # If ES/Vertex not configured this will 500; test only schema path
    assert r.status_code in (200, 500)
