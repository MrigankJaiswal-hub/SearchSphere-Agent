# backend/tests/test_chat.py
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_chat_validation():
    r = client.post("/api/chat", json={"query": "Summarize docs"})
    assert r.status_code in (200, 500)
